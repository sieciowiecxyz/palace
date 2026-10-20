// SPDX-License-Identifier: Apache-2.0

#include "cudss.hpp"

#if defined(MFEM_USE_CUDSS)

#if defined(MFEM_USE_CUDA) && !defined(__CUDACC__)
#error "Compile this file as CUDA: MFEM SparseMatrix ABI depends on CUDA_VERSION"
#endif
#include <cudss.h>
#include <cuda_runtime_api.h>
#include <cmath>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <map>
#include <string_view>
#include "linalg/rap.hpp"

namespace palace
{
namespace
{

void Check(cudssStatus_t status, const char *operation = "cuDSS API")
{
  MFEM_VERIFY(status == CUDSS_STATUS_SUCCESS, "Native complex cuDSS error in " << operation << ": " << int(status));
}

void Sync()
{
  const auto status = cudaDeviceSynchronize();
  MFEM_VERIFY(status == cudaSuccess, "Native complex CUDA error: " << cudaGetErrorString(status));
}

bool Enabled(const char *name)
{
  const char *value = std::getenv(name);
  return value && std::string_view(value) == "1";
}

}  // namespace

struct ComplexCuDSSSolver::Impl
{
  cudssHandle_t handle = nullptr;
  cudssConfig_t config = nullptr;
  cudssData_t data = nullptr;
  cudssMatrix_t matrix = nullptr, rhs_matrix = nullptr, solution_matrix = nullptr;
  mfem::Array<int> offsets, columns;
  Vector values;
  mutable Vector rhs, solution;

  Impl()
  {
    values.UseDevice(true);
    rhs.UseDevice(true);
    solution.UseDevice(true);
  }

  void Clear()
  {
    if (handle) Sync();
    if (data) Check(cudssDataDestroy(handle, data));
    if (matrix) Check(cudssMatrixDestroy(matrix));
    if (rhs_matrix) Check(cudssMatrixDestroy(rhs_matrix));
    if (solution_matrix) Check(cudssMatrixDestroy(solution_matrix));
    if (config) Check(cudssConfigDestroy(config));
    if (handle) Check(cudssDestroy(handle));
    handle = nullptr;
    config = nullptr;
    data = nullptr;
    matrix = rhs_matrix = solution_matrix = nullptr;
  }

  ~Impl() { Clear(); }
};

ComplexCuDSSSolver::ComplexCuDSSSolver(MPI_Comm comm, bool drop)
  : Solver<ComplexOperator>(false), impl(std::make_unique<Impl>()), drop_small_entries(drop)
{
  MFEM_VERIFY(Mpi::Size(comm) == 1 && mfem::Device::Allows(mfem::Backend::CUDA_MASK),
              "Native complex coarse requires one MPI rank and CUDA!");
  MFEM_VERIFY(!Enabled("PALACE_CUDSS_FP32") && !Enabled("PALACE_CUDSS_HYBRID_EXECUTE"),
              "Native complex coarse requires FP64 factors and GPU execution!");
}

ComplexCuDSSSolver::~ComplexCuDSSSolver() = default;

void ComplexCuDSSSolver::SetOperator(const ComplexOperator &op)
{
  const int n = op.Height();
  MFEM_VERIFY(n > 0 && n == op.Width() && n <= std::numeric_limits<int>::max() / 2,
              "Invalid native complex coarse dimension!");
  impl->Clear();  // Prototype: rebuild analysis, no symbolic reuse claim.

  const auto *ar = dynamic_cast<const mfem::HypreParMatrix *>(op.Real());
  const auto *ai = dynamic_cast<const mfem::HypreParMatrix *>(op.Imag());
  const auto *pr = op.Real() && !ar ? dynamic_cast<const ParOperator *>(op.Real()) : nullptr;
  const auto *pi = op.Imag() && !ai ? dynamic_cast<const ParOperator *>(op.Imag()) : nullptr;
  MFEM_VERIFY((!op.Real() || ar || pr) && (!op.Imag() || ai || pi),
              "Native complex coarse requires parallel-assembled real/imag operators!");
  if (pr) ar = &pr->ParallelAssemble();
  if (pi) ai = &pi->ParallelAssemble();
  MFEM_VERIFY(ar || ai, "Empty native complex coarse operator!");
  MFEM_VERIFY((!ar || (ar->Height() == n && ar->Width() == n)) &&
                  (!ai || (ai->Height() == n && ai->Width() == n)),
              "Mismatched native complex coarse parts!");
  mfem::SparseMatrix real, imag;
  if (ar) ar->GetDiag(real);
  if (ai) ai->GetDiag(imag);
  const int *ri = ar ? real.HostReadI() : nullptr, *rj = ar ? real.HostReadJ() : nullptr;
  const int *ii = ai ? imag.HostReadI() : nullptr, *ij = ai ? imag.HostReadJ() : nullptr;
  const double *rv = ar ? real.HostReadData() : nullptr, *iv = ai ? imag.HostReadData() : nullptr;
  std::vector<int> offsets(n + 1), columns;
  std::vector<double> values;
  const double threshold = drop_small_entries ? std::pow(std::numeric_limits<double>::epsilon(), 2) : -1.0;
  for (int row = 0; row < n; ++row)
  {
    offsets[row] = int(columns.size());
    std::map<int, std::complex<double>> merged;
    if (ar) for (int k = ri[row]; k < ri[row + 1]; ++k) merged[rj[k]] += rv[k];
    if (ai) for (int k = ii[row]; k < ii[row + 1]; ++k) merged[ij[k]] += std::complex<double>(0, iv[k]);
    for (auto [column, value] : merged)
    {
      MFEM_VERIFY(column >= 0 && column < n, "Invalid single-rank coarse column!");
      if (std::abs(value.real()) < threshold) value.real(0.0);
      if (std::abs(value.imag()) < threshold) value.imag(0.0);
      if (drop_small_entries && value == 0.0) continue;
      MFEM_VERIFY(values.size() + 2 <= size_t(std::numeric_limits<int>::max()),
                  "Native complex CSR exceeds supported int-sized MFEM storage!");
      columns.push_back(column);
      values.push_back(value.real());
      values.push_back(value.imag());
    }
  }
  offsets[n] = int(columns.size());
  const bool audit = std::getenv("PALACE_PORT_SETUP_AUDIT") != nullptr;
  if (audit)
  {
    const auto hash = [](std::uint64_t h, const auto &v) {
      const auto *p = reinterpret_cast<const unsigned char *>(v.data());
      for (std::size_t i = 0; i < v.size() * sizeof(v[0]); ++i) h = (h ^ p[i]) * 1099511628211ULL;
      return h;
    };
    constexpr std::uint64_t seed = 14695981039346656037ULL;
    Mpi::Print("PALACE_COARSE_CSR: algorithm=fnv1a64 structure={:016x} values={:016x}\n",
               hash(hash(seed, offsets), columns), hash(seed, values));
  }
  impl->offsets.SetSize(n + 1);
  impl->columns.SetSize(int(columns.size()));
  impl->values.SetSize(int(values.size()));
  std::copy(offsets.begin(), offsets.end(), impl->offsets.HostWrite());
  std::copy(columns.begin(), columns.end(), impl->columns.HostWrite());
  std::copy(values.begin(), values.end(), impl->values.HostWrite());
  // Release assembly and temporary host copies before factorization.
  real.Clear();
  imag.Clear();
  if (pr) pr->StealParallelAssemble();
  if (pi) pi->StealParallelAssemble();
  offsets.clear(); offsets.shrink_to_fit();
  columns.clear(); columns.shrink_to_fit();
  values.clear(); values.shrink_to_fit();
  impl->rhs.SetSize(2 * n);
  impl->solution.SetSize(2 * n);
  Check(cudssCreate(&impl->handle));
  Check(cudssConfigCreate(&impl->config));
  Check(cudssDataCreate(impl->handle, &impl->data));
  // A complex-symmetric Maxwell matrix is not generally Hermitian. Use GENERAL.
  Check(cudssMatrixCreateCsr(&impl->matrix, n, n, impl->columns.Size(),
                            const_cast<int *>(impl->offsets.Read()), nullptr,
                            const_cast<int *>(impl->columns.Read()),
                            const_cast<double *>(impl->values.Read()), CUDA_R_32I, CUDA_C_64F,
                            CUDSS_MTYPE_GENERAL, CUDSS_MVIEW_FULL, CUDSS_BASE_ZERO));
  Check(cudssMatrixCreateDn(&impl->rhs_matrix, n, 1, n, impl->rhs.Write(), CUDA_C_64F,
                           CUDSS_LAYOUT_COL_MAJOR));
  Check(cudssMatrixCreateDn(&impl->solution_matrix, n, 1, n, impl->solution.Write(), CUDA_C_64F,
                           CUDSS_LAYOUT_COL_MAJOR));
  Sync();
  const auto analysis_begin = std::chrono::steady_clock::now();
  Check(cudssExecute(impl->handle, CUDSS_PHASE_ANALYSIS, impl->config, impl->data,
                    impl->matrix, impl->solution_matrix, impl->rhs_matrix), "analysis");
  if (audit) Sync();
  if (std::getenv("PALACE_CUDSS_HYBRID_MIB"))
  {
    Sync();
    int mode = 0;
    const char *request = std::getenv("PALACE_CUDSS_HYBRID_MIB");
    char *end = nullptr;
    const long long mib = std::strtoll(request, &end, 10);
    MFEM_VERIFY(request[0] && !*end && mib >= 256 && mib <= 16384, "Invalid hybrid MiB budget!");
    int64_t limit = mib * 1024 * 1024, observed_limit = 0, minimum = 0, estimates[16]{};
    size_t written = 0;
    Check(cudssConfigGet(impl->config, CUDSS_CONFIG_HYBRID_MODE, &mode, sizeof(mode), &written));
    MFEM_VERIFY(written == sizeof(mode) && mode == 1, "Hybrid memory adapter was not applied!");
    Check(cudssDataGet(impl->handle, impl->data, CUDSS_DATA_HYBRID_DEVICE_MEMORY_MIN,
                      &minimum, sizeof(minimum), &written), "hybrid minimum query");
    MFEM_VERIFY(written == sizeof(minimum) && minimum >= 0, "Invalid hybrid minimum query!");
    Check(cudssDataGet(impl->handle, impl->data, CUDSS_DATA_MEMORY_ESTIMATES,
                      estimates, sizeof(estimates), &written), "hybrid estimates query");
    MFEM_VERIFY(written >= 6 * sizeof(int64_t) && estimates[5] >= 0,
                "Invalid hybrid host estimate!");
    Mpi::Print("PALACE_NATIVE_HYBRID_REQUIREMENT: requested_bytes={} minimum_device_bytes={} estimated_host_bytes={}\n",
               limit, minimum, estimates[5]);
    MFEM_VERIFY(minimum <= limit, "Hybrid device minimum exceeds requested budget; not factorizing!");
    Check(cudssConfigSet(impl->config, CUDSS_CONFIG_HYBRID_DEVICE_MEMORY_LIMIT,
                         &limit, sizeof(limit)), "hybrid limit after analysis");
    Check(cudssConfigGet(impl->config, CUDSS_CONFIG_HYBRID_DEVICE_MEMORY_LIMIT,
                         &observed_limit, sizeof(observed_limit), &written));
    MFEM_VERIFY(written == sizeof(observed_limit) && observed_limit == limit,
                "Hybrid device budget was not applied!");
    Mpi::Print("PALACE_NATIVE_HYBRID: limit_bytes={} minimum_device_bytes={} estimated_host_bytes={}\n",
               observed_limit, minimum, estimates[5]);
  }
  const auto factor_begin = std::chrono::steady_clock::now();
  Check(cudssExecute(impl->handle, CUDSS_PHASE_FACTORIZATION, impl->config, impl->data,
                    impl->matrix, impl->solution_matrix, impl->rhs_matrix), "factorization");
  Sync();
  if (audit)
  {
    const auto end = std::chrono::steady_clock::now();
    Mpi::Print("PALACE_COARSE_SETUP: analysis_s={:.9e} factor_s={:.9e}\n",
               std::chrono::duration<double>(factor_begin - analysis_begin).count(),
               std::chrono::duration<double>(end - factor_begin).count());
  }
  int info = 0;
  size_t written = 0;
  Check(cudssDataGet(impl->handle, impl->data, CUDSS_DATA_INFO, &info, sizeof(info), &written));
  MFEM_VERIFY(info == 0, "Native complex cuDSS factorization device error: " << info);
  height = width = n;
  Mpi::Print("PALACE_NATIVE_COMPLEX_COARSE: dimension={} nnz={} dtype=complex_fp64 matrix=general\n",
             n, impl->columns.Size());
}

void ComplexCuDSSSolver::Mult(const ComplexVector &x, ComplexVector &y) const
{
  MFEM_VERIFY(impl->handle && x.Size() == width && y.Size() == height,
              "Uninitialized or mismatched native complex coarse solve!");
  x.Get(reinterpret_cast<std::complex<double> *>(impl->rhs.Write()), width, true);
  Check(cudssMatrixSetValues(impl->rhs_matrix, impl->rhs.Write()));
  Check(cudssMatrixSetValues(impl->solution_matrix, impl->solution.Write()));
  Sync();
  Check(cudssExecute(impl->handle, CUDSS_PHASE_SOLVE, impl->config, impl->data,
                    impl->matrix, impl->solution_matrix, impl->rhs_matrix));
  Sync();
  y.Set(reinterpret_cast<const std::complex<double> *>(impl->solution.Read()), height, true);
  Sync();
}

}  // namespace palace

#endif
