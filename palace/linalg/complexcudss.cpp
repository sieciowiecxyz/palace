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
#include <algorithm>
#include <complex>
#include <utility>
#include <vector>
#include <string_view>
#include "linalg/rap.hpp"
#include "linalg/mixedcoarse.hpp"

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

void CheckCuda(cudaError_t status)
{
  MFEM_VERIFY(status == cudaSuccess, "Mixed coarse CUDA error: " << cudaGetErrorString(status));
}

bool Enabled(const char *name)
{
  const char *value = std::getenv(name);
  return value && std::string_view(value) == "1";
}

int FixedCorrections(bool mixed)
{
  const char *value = std::getenv("PALACE_NATIVE_COARSE_CORRECTIONS");
  if (!value) return 2;
  MFEM_VERIFY(mixed, "Fixed coarse corrections require native mixed precision!");
  const std::string_view count(value);
  MFEM_VERIFY(count == "2" || count == "3" || count == "4",
              "Fixed coarse corrections must be 2, 3 or 4!");
  return value[0] - '0';
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
  MPI_Comm comm;
  const bool mixed = Enabled("PALACE_NATIVE_COARSE_FP32");
  // The driven coarse matrix is complex symmetric (A^T = A, not Hermitian): LDL^T on the
  // upper triangle needs about half the factor memory and work of a general LU.
  // PALACE_COARSE_GENERAL=1 restores the general LU on the full matrix.
  const bool symmetric = !mixed && !std::getenv("PALACE_COARSE_GENERAL");
  // The sparsity is the same at every frequency: keep the symbolic analysis and only
  // refactorize. PALACE_COARSE_NO_REUSE=1 restores a full rebuild per operator.
  const bool reuse = !mixed && !std::getenv("PALACE_COARSE_NO_REUSE") &&
                     !std::getenv("PALACE_CUDSS_HYBRID_MIB");
  const int corrections = FixedCorrections(mixed);
  Vector scale;
  mutable Vector residual;
  mfem::Array<cuComplex> float_values;
  mutable mfem::Array<cuComplex> float_rhs, float_solution;
  mutable mfem::Array<int> invalid;
  mutable unsigned long long solves = 0;
  mutable double max_residual = 0.0;

  explicit Impl(MPI_Comm comm_) : comm(comm_)
  {
    values.UseDevice(true);
    rhs.UseDevice(true);
    solution.UseDevice(true);
    scale.UseDevice(true);
    residual.UseDevice(true);
  }

  void Clear()
  {
    if (handle) Sync();
    if (handle && mixed && solves)
      Mpi::Print("PALACE_NATIVE_MIXED_COARSE: solves={} corrections={} max_relative_residual={:.9e} backend=cuda_fp64\n",
                 solves, corrections, max_residual);
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
    solves = 0;
    max_residual = 0.0;
  }

  ~Impl() { Clear(); }
};

ComplexCuDSSSolver::ComplexCuDSSSolver(MPI_Comm comm, bool drop)
  : Solver<ComplexOperator>(false), impl(std::make_unique<Impl>(comm)), drop_small_entries(drop)
{
  MFEM_VERIFY(Mpi::Size(comm) == 1 && mfem::Device::Allows(mfem::Backend::CUDA_MASK),
              "Native complex coarse requires one MPI rank and CUDA!");
  MFEM_VERIFY(!Enabled("PALACE_CUDSS_FP32") && !Enabled("PALACE_CUDSS_HYBRID_EXECUTE"),
              "Native complex coarse cannot use the real FP32 shim or CPU hybrid execution!");
  MFEM_VERIFY(!impl->mixed || !std::getenv("PALACE_CUDSS_HYBRID_MIB"),
              "Mixed coarse cannot combine hybrid memory in this prototype!");
}

ComplexCuDSSSolver::~ComplexCuDSSSolver() = default;

void ComplexCuDSSSolver::SetOperator(const ComplexOperator &op)
{
  const int n = op.Height();
  MFEM_VERIFY(n > 0 && n == op.Width() && n <= std::numeric_limits<int>::max() / 2,
              "Invalid native complex coarse dimension!");
  const auto merge_begin = std::chrono::steady_clock::now();

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
  std::vector<double> scales(impl->mixed ? n : 0);
  const double threshold = drop_small_entries ? std::pow(std::numeric_limits<double>::epsilon(), 2) : -1.0;
  std::vector<std::pair<int, std::complex<double>>> entries;
  for (int row = 0; row < n; ++row)
  {
    offsets[row] = int(columns.size());
    entries.clear();
    if (ar) for (int k = ri[row]; k < ri[row + 1]; ++k) entries.emplace_back(rj[k], rv[k]);
    if (ai) for (int k = ii[row]; k < ii[row + 1]; ++k)
      entries.emplace_back(ij[k], std::complex<double>(0, iv[k]));
    std::sort(entries.begin(), entries.end(),
              [](const auto &a, const auto &b) { return a.first < b.first; });
    for (std::size_t first = 0; first < entries.size();)
    {
      const int column = entries[first].first;
      std::complex<double> value = 0.0;
      for (; first < entries.size() && entries[first].first == column; ++first)
        value += entries[first].second;
      MFEM_VERIFY(column >= 0 && column < n, "Invalid single-rank coarse column!");
      if (impl->symmetric && column < row) continue;
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
  if (impl->mixed)
  {
    // Equilibrate the exact stored coarse CSR, including the existing drop policy.
    for (int row = 0; row < n; ++row)
    {
      double diagonal = 0.0, row_max = 0.0;
      for (int j = offsets[row]; j < offsets[row + 1]; ++j)
      {
        const double magnitude = std::hypot(values[2*j], values[2*j+1]);
        MFEM_VERIFY(std::isfinite(magnitude), "Nonfinite original mixed coarse CSR!");
        row_max = std::max(row_max, magnitude);
        if (columns[j] == row) diagonal = magnitude;
      }
      scales[row] = mixedcoarse::Scale(diagonal, row_max);
      MFEM_VERIFY(std::isfinite(scales[row]) && scales[row] > 0.0,
                  "Mixed coarse cannot scale an empty/invalid row!");
    }
    for (int row = 0; row < n; ++row)
      for (int j = offsets[row]; j < offsets[row + 1]; ++j)
      {
        const double d = scales[row] * scales[columns[j]];
        MFEM_VERIFY(std::isfinite(float(d * values[2*j])) && std::isfinite(float(d * values[2*j+1])),
                    "Mixed coarse matrix overflows FP32 after scaling!");
      }
    impl->scale.SetSize(n);
    std::copy(scales.begin(), scales.end(), impl->scale.HostWrite());
    const auto range = std::minmax_element(scales.begin(), scales.end());
    Mpi::Print("PALACE_NATIVE_MIXED_SCALE: min={:.9e} max={:.9e} corrections={} original=complex_fp64\n",
               *range.first, *range.second, impl->corrections);
  }
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
  const auto merge_end = std::chrono::steady_clock::now();
  if (impl->reuse && impl->handle && impl->offsets.Size() == n + 1 &&
      impl->columns.Size() == int(columns.size()) &&
      std::equal(offsets.begin(), offsets.end(), impl->offsets.HostRead()) &&
      std::equal(columns.begin(), columns.end(), impl->columns.HostRead()))
  {
    // Same sparsity as the factorized operator: new values, same symbolic analysis.
    std::copy(values.begin(), values.end(), impl->values.HostWrite());
    real.Clear();
    imag.Clear();
    if (pr) pr->StealParallelAssemble();
    if (pi) pi->StealParallelAssemble();
    Check(cudssMatrixSetValues(impl->matrix, const_cast<double *>(impl->values.Read())));
    Sync();
    const auto factor_begin = std::chrono::steady_clock::now();
    Check(cudssExecute(impl->handle, CUDSS_PHASE_FACTORIZATION, impl->config, impl->data,
                      impl->matrix, impl->solution_matrix, impl->rhs_matrix),
          "factorization with reused analysis");
    Sync();
    int info = 0;
    size_t written = 0;
    Check(cudssDataGet(impl->handle, impl->data, CUDSS_DATA_INFO, &info, sizeof(info), &written));
    MFEM_VERIFY(written == sizeof(info) && info == 0,
                "Native complex cuDSS refactorization device error: " << info);
    Mpi::Print("PALACE_COARSE_SETUP: merge_s={:.3f} analysis_s=reused factor_s={:.3f}\n",
               std::chrono::duration<double>(merge_end - merge_begin).count(),
               std::chrono::duration<double>(std::chrono::steady_clock::now() - factor_begin).count());
    return;
  }
  impl->Clear();
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
  const auto dtype = impl->mixed ? CUDA_C_32F : CUDA_C_64F;
  void *matrix_values = const_cast<double *>(impl->values.Read());
  void *rhs_values = impl->rhs.Write(), *solution_values = impl->solution.Write();
  if (impl->mixed)
  {
    // Built-in same-dtype refinement is explicitly disabled: all corrections below
    // use the original FP64 CSR. A fixed count preserves the chosen PC structure.
    int refinement = 0;
    Check(cudssConfigSet(impl->config, CUDSS_CONFIG_IR_N_STEPS, &refinement, sizeof(refinement)));
    impl->float_values.SetSize(impl->columns.Size());
    impl->float_rhs.SetSize(n);
    impl->float_solution.SetSize(n);
    impl->residual.SetSize(2*n);
    impl->invalid.SetSize(1);
    CheckCuda(mixedcoarse::MatrixPack(n, impl->offsets.Read(), impl->columns.Read(),
        reinterpret_cast<const cuDoubleComplex *>(impl->values.Read()), impl->scale.Read(),
        impl->float_values.Write()));
    matrix_values = impl->float_values.Write();
    rhs_values = impl->float_rhs.Write();
    solution_values = impl->float_solution.Write();
  }
  // A complex-symmetric Maxwell matrix is not Hermitian: SYMMETRIC (LDL^T), never HERMITIAN.
  Check(cudssMatrixCreateCsr(&impl->matrix, n, n, impl->columns.Size(),
                            const_cast<int *>(impl->offsets.Read()), nullptr,
                            const_cast<int *>(impl->columns.Read()),
                            matrix_values, CUDA_R_32I, dtype,
                            impl->symmetric ? CUDSS_MTYPE_SYMMETRIC : CUDSS_MTYPE_GENERAL,
                            impl->symmetric ? CUDSS_MVIEW_UPPER : CUDSS_MVIEW_FULL,
                            CUDSS_BASE_ZERO));
  Check(cudssMatrixCreateDn(&impl->rhs_matrix, n, 1, n, rhs_values, dtype,
                           CUDSS_LAYOUT_COL_MAJOR));
  Check(cudssMatrixCreateDn(&impl->solution_matrix, n, 1, n, solution_values, dtype,
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
  Mpi::Print("PALACE_COARSE_SETUP: merge_s={:.3f} analysis_s={:.3f} factor_s={:.3f}\n",
             std::chrono::duration<double>(merge_end - merge_begin).count(),
             std::chrono::duration<double>(factor_begin - analysis_begin).count(),
             std::chrono::duration<double>(std::chrono::steady_clock::now() - factor_begin).count());
  int info = 0;
  size_t written = 0;
  Check(cudssDataGet(impl->handle, impl->data, CUDSS_DATA_INFO, &info, sizeof(info), &written));
  MFEM_VERIFY(written == sizeof(info) && info == 0, "Native complex cuDSS factorization device error: " << info);
  height = width = n;
  Mpi::Print("PALACE_NATIVE_COMPLEX_COARSE: dimension={} nnz={} dtype={} matrix={}\n",
             n, impl->columns.Size(), impl->mixed ? "complex_fp32" : "complex_fp64",
             impl->symmetric ? "symmetric_upper" : "general");
}

void ComplexCuDSSSolver::Mult(const ComplexVector &x, ComplexVector &y) const
{
  MFEM_VERIFY(impl->handle && x.Size() == width && y.Size() == height,
              "Uninitialized or mismatched native complex coarse solve!");
  x.Get(reinterpret_cast<std::complex<double> *>(impl->rhs.Write()), width, true);
  if (impl->mixed)
  {
    const auto *b = reinterpret_cast<const cuDoubleComplex *>(impl->rhs.Read());
    auto *s = reinterpret_cast<cuDoubleComplex *>(impl->solution.Write());
    // Keep a fixed count for every apply: no residual-dependent PC changes in GMRES.
    for (int step = 0; step <= impl->corrections; ++step)
    {
      auto *r = reinterpret_cast<cuDoubleComplex *>(impl->residual.Write());
      if (step) CheckCuda(mixedcoarse::Residual(width, 1, impl->offsets.Read(), impl->columns.Read(),
          reinterpret_cast<const cuDoubleComplex *>(impl->values.Read()), s, b, r));
      CheckCuda(cudaMemset(impl->invalid.Write(), 0, sizeof(int)));
      CheckCuda(mixedcoarse::Pack(width, 1, impl->scale.Read(), step ? r : b,
          impl->float_rhs.Write(), nullptr, impl->invalid.Write()));
      Sync();
      MFEM_VERIFY(impl->invalid.HostRead()[0] == 0, "Mixed coarse RHS conversion overflow/nonfinite!");
      Check(cudssExecute(impl->handle, CUDSS_PHASE_SOLVE, impl->config, impl->data,
          impl->matrix, impl->solution_matrix, impl->rhs_matrix), "FP32 solve/correction");
      CheckCuda(mixedcoarse::Accumulate(width, 1, impl->scale.Read(), impl->float_solution.Read(), s, step != 0));
      Sync();
    }
    CheckCuda(mixedcoarse::Residual(width, 1, impl->offsets.Read(), impl->columns.Read(),
        reinterpret_cast<const cuDoubleComplex *>(impl->values.Read()), s, b,
        reinterpret_cast<cuDoubleComplex *>(impl->residual.Write())));
    Sync();
    const double rn = linalg::Norml2(impl->comm, impl->residual), bn = linalg::Norml2(impl->comm, impl->rhs);
    const double relative = bn > 0.0 ? rn / bn : rn;
    MFEM_VERIFY(std::isfinite(rn) && std::isfinite(bn) && std::isfinite(relative) && relative <= 1e-3,
                "Mixed coarse original FP64 residual failed: " << relative);
    impl->max_residual = std::max(impl->max_residual, relative);
    ++impl->solves;
    y.Set(reinterpret_cast<const std::complex<double> *>(impl->solution.Read()), height, true);
    Sync();
    return;
  }
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
