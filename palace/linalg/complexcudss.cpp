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

bool MixedRequested()
{
  const char *value = std::getenv("PALACE_NATIVE_COARSE_FP32");
  MFEM_VERIFY(!value || std::string_view(value) == "0" || std::string_view(value) == "1",
              "PALACE_NATIVE_COARSE_FP32 must be 0 (FP64) or 1 (mixed)!");
  return !value || std::string_view(value) == "1";
}

void ConfigureThreading(cudssHandle_t handle, cudssConfig_t config)
{
  const char *request = std::getenv("PALACE_CUDSS_HOST_NTHREADS");
  if (!request) return;
  char *end = nullptr;
  const long count = std::strtol(request, &end, 10);
  MFEM_VERIFY(request[0] && !*end && count >= 1 && count <= 256,
              "PALACE_CUDSS_HOST_NTHREADS must be an integer in [1,256]!");
  const char *layer = std::getenv("CUDSS_THREADING_LIB");
  if (!layer) layer = "libcudss_mtlayer_gomp.so";
  Check(cudssSetThreadingLayer(handle, layer), "initialize threading layer");
  int threads = int(count);
  Check(cudssConfigSet(config, CUDSS_CONFIG_HOST_NTHREADS, &threads, sizeof(threads)),
        "host thread count");
  // cuDSS 0.7.1 accepts HOST_NTHREADS, but its getter returns INTERNAL_ERROR.
  Mpi::Print("PALACE_CUDSS_THREADING: layer={} host_nthreads={}\n", layer, threads);
}

void ConfigureTuning(cudssConfig_t config)
{
  // Optional cuDSS tuning; unset keeps the library defaults.
  if (const char *levels = std::getenv("PALACE_CUDSS_ND_NLEVELS"))
  {
    int value = std::atoi(levels);
    Check(cudssConfigSet(config, CUDSS_CONFIG_ND_NLEVELS, &value, sizeof(value)),
          "nested dissection levels");
  }
  if (const char *algorithm = std::getenv("PALACE_CUDSS_REORDERING"))
  {
    cudssAlgType_t value = cudssAlgType_t(CUDSS_ALG_DEFAULT + std::atoi(algorithm));
    Check(cudssConfigSet(config, CUDSS_CONFIG_REORDERING_ALG, &value, sizeof(value)),
          "reordering algorithm");
  }
}

int FixedCorrections(bool mixed)
{
  const char *value = std::getenv("PALACE_NATIVE_COARSE_CORRECTIONS");
  if (!value) return 2;
  MFEM_VERIFY(mixed, "Fixed coarse corrections require native mixed precision!");
  const std::string_view count(value);
  MFEM_VERIFY(count == "0" || count == "1" || count == "2" || count == "3" || count == "4",
              "Fixed coarse corrections must be in [0,4]!");
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
  const bool mixed = MixedRequested();
  bool effective_mixed = mixed;
  // Latch accurate recovery for this solver lifetime, including later frequencies.
  const char *fallback_reason = "none";
  int fp64_refinement = 0;
  // The driven coarse matrix is complex symmetric (A^T = A, not Hermitian): LDL^T on the
  // upper triangle needs about half the factor memory and work of a general LU.
  // PALACE_COARSE_GENERAL=1 restores the general LU on the full matrix.
  const bool symmetric = !std::getenv("PALACE_COARSE_GENERAL");
  // The sparsity is the same at every frequency: keep the symbolic analysis and only
  // refactorize. PALACE_COARSE_NO_REUSE=1 restores a full rebuild per operator.
  const bool reuse = !std::getenv("PALACE_COARSE_NO_REUSE") &&
                     !std::getenv("PALACE_CUDSS_HYBRID_MIB");
  // Mixed + symmetric: cuDSS gets the FP32 upper triangle, while the FP64 corrections
  // keep the full CSR in offsets/columns/values.
  mfem::Array<int> upper_offsets, upper_columns;
  Vector upper_values;
  const int corrections = FixedCorrections(mixed);
  Vector scale;
  mutable Vector residual;
  mfem::Array<cuComplex> float_values;
  mutable mfem::Array<cuComplex> float_rhs, float_solution;
  mutable mfem::Array<int> invalid;
  mutable unsigned long long solves = 0;
  mutable unsigned long long generation_solves = 0;
  mutable double max_residual = 0.0;

  explicit Impl(MPI_Comm comm_) : comm(comm_)
  {
    values.UseDevice(true);
    upper_values.UseDevice(true);
    rhs.UseDevice(true);
    solution.UseDevice(true);
    scale.UseDevice(true);
    residual.UseDevice(true);
  }

  void Clear()
  {
    if (handle) Sync();
    if (handle && mixed && solves)
      Mpi::Print("PALACE_NATIVE_MIXED_COARSE: solves={} corrections={} max_relative_residual={:.9e} backend=cuda_fp64 effectiveprecision={} fallback_reason={}\n",
                 solves, corrections, max_residual,
                 effective_mixed ? "fp32_factors_fp64_corrections" : "fp64", fallback_reason);
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
    generation_solves = 0;
    solves = 0;
    max_residual = 0.0;
  }

  void Recover(const char *reason)
  {
    MFEM_VERIFY(mixed && effective_mixed, "Invalid native precision recovery state!");
    const auto begin = std::chrono::steady_clock::now();
    Sync();
    // Destroy factors before allocating FP64 factors. Never retain both factor sets.
    Check(cudssDataDestroy(handle, data));
    data = nullptr;
    Check(cudssMatrixDestroy(matrix));
    Check(cudssMatrixDestroy(rhs_matrix));
    Check(cudssMatrixDestroy(solution_matrix));
    matrix = rhs_matrix = solution_matrix = nullptr;
    float_values.DeleteAll();
    float_rhs.DeleteAll();
    float_solution.DeleteAll();
    effective_mixed = false;
    fallback_reason = reason;
    // cuDSS 0.7.1 CUDSS-1019: changing matrix dtype with a reused handle
    // produces incorrect results or crashes. Recreate the handle, not only data.
    Check(cudssConfigDestroy(config));
    config = nullptr;
    Check(cudssDestroy(handle));
    handle = nullptr;
    Check(cudssCreate(&handle));
    Check(cudssConfigCreate(&config));
    ConfigureThreading(handle, config);
    Check(cudssDataCreate(handle, &data));
    ConfigureTuning(config);
    // Restore cuDSS's default FP64 refinement (disabled only for our mixed factors).
    int refinement = fp64_refinement;
    Check(cudssConfigSet(config, CUDSS_CONFIG_IR_N_STEPS, &refinement, sizeof(refinement)));
    const auto &oi = symmetric ? upper_offsets : offsets;
    const auto &oj = symmetric ? upper_columns : columns;
    auto &av = symmetric ? upper_values : values;
    const int n = offsets.Size() - 1;
    Check(cudssMatrixCreateCsr(&matrix, n, n, oj.Size(), const_cast<int *>(oi.Read()),
        nullptr, const_cast<int *>(oj.Read()), const_cast<double *>(av.Read()), CUDA_R_32I,
        CUDA_C_64F, symmetric ? CUDSS_MTYPE_SYMMETRIC : CUDSS_MTYPE_GENERAL,
        symmetric ? CUDSS_MVIEW_UPPER : CUDSS_MVIEW_FULL, CUDSS_BASE_ZERO));
    Check(cudssMatrixCreateDn(&rhs_matrix, n, 1, n, rhs.Write(), CUDA_C_64F, CUDSS_LAYOUT_COL_MAJOR));
    Check(cudssMatrixCreateDn(&solution_matrix, n, 1, n, solution.Write(), CUDA_C_64F, CUDSS_LAYOUT_COL_MAJOR));
    Check(cudssExecute(handle, CUDSS_PHASE_ANALYSIS, config, data, matrix, solution_matrix, rhs_matrix),
          "FP64 recovery analysis");
    Check(cudssExecute(handle, CUDSS_PHASE_FACTORIZATION, config, data, matrix, solution_matrix, rhs_matrix),
          "FP64 recovery factorization");
    Sync();
    int info = 0;
    size_t written = 0;
    Check(cudssDataGet(handle, data, CUDSS_DATA_INFO, &info, sizeof(info), &written));
    MFEM_VERIFY(written == sizeof(info) && info == 0, "FP64 recovery factorization failed: " << info);
    Mpi::Print("PALACE_NATIVE_COARSE_RECOVERY: requestedprecision=fp32 effectiveprecision=fp64 reason={} rebuild_s={:.6f}\n",
               reason, std::chrono::duration<double>(std::chrono::steady_clock::now() - begin).count());
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
  impl->generation_solves = 0;
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
  // offsets/columns/values: the full matrix when it is needed (general LU, or the FP64
  // residual of the mixed mode), else only the upper triangle. upper_*: the cuDSS input
  // of the symmetric mixed mode.
  const bool keep_full = impl->mixed || !impl->symmetric;
  const bool keep_upper = impl->mixed && impl->symmetric;
  std::vector<int> upper_offsets(keep_upper ? n + 1 : 0), upper_columns;
  std::vector<double> upper_values;
  const double threshold = drop_small_entries ? std::pow(std::numeric_limits<double>::epsilon(), 2) : -1.0;
  std::vector<std::pair<int, std::complex<double>>> entries;
  for (int row = 0; row < n; ++row)
  {
    offsets[row] = int(columns.size());
    if (keep_upper) upper_offsets[row] = int(upper_columns.size());
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
      if (std::abs(value.real()) < threshold) value.real(0.0);
      if (std::abs(value.imag()) < threshold) value.imag(0.0);
      if (drop_small_entries && value == 0.0) continue;
      if (keep_upper && column >= row)
      {
        upper_columns.push_back(column);
        upper_values.push_back(value.real());
        upper_values.push_back(value.imag());
      }
      if (!keep_full && column < row) continue;
      MFEM_VERIFY(values.size() + 2 <= size_t(std::numeric_limits<int>::max()),
                  "Native complex CSR exceeds supported int-sized MFEM storage!");
      columns.push_back(column);
      values.push_back(value.real());
      values.push_back(value.imag());
    }
  }
  offsets[n] = int(columns.size());
  if (keep_upper) upper_offsets[n] = int(upper_columns.size());
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
        if (impl->effective_mixed &&
            (!std::isfinite(float(d * values[2*j])) || !std::isfinite(float(d * values[2*j+1]))))
        {
          // A previous frequency may still own FP32 descriptors; discard them
          // before choosing FP64 so symbolic reuse never crosses data types.
          impl->Clear();
          impl->effective_mixed = false;
          impl->fallback_reason = "matrix_conversion";
          Mpi::Print("PALACE_NATIVE_COARSE_RECOVERY: requestedprecision=fp32 effectiveprecision=fp64 reason=matrix_conversion rebuild_s=0\n");
        }
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
  // Scaled FP32 values of the cuDSS matrix (mixed mode), from the arrays already stored
  // in impl; returns the device pointer.
  const auto pack_mixed = [&]() -> void *
  {
    if (keep_upper)
    {
      impl->upper_values.UseDevice(true);
      impl->upper_values.SetSize(int(upper_values.size()));
      std::copy(upper_values.begin(), upper_values.end(), impl->upper_values.HostWrite());
      impl->float_values.SetSize(impl->upper_columns.Size());
      CheckCuda(mixedcoarse::MatrixPack(n, impl->upper_offsets.Read(), impl->upper_columns.Read(),
          reinterpret_cast<const cuDoubleComplex *>(impl->upper_values.Read()), impl->scale.Read(),
          impl->float_values.Write()));
    }
    else
    {
      impl->float_values.SetSize(impl->columns.Size());
      CheckCuda(mixedcoarse::MatrixPack(n, impl->offsets.Read(), impl->columns.Read(),
          reinterpret_cast<const cuDoubleComplex *>(impl->values.Read()), impl->scale.Read(),
          impl->float_values.Write()));
    }
    return impl->float_values.Write();
  };
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
    if (keep_upper && !impl->effective_mixed)
    {
      impl->upper_values.SetSize(int(upper_values.size()));
      std::copy(upper_values.begin(), upper_values.end(), impl->upper_values.HostWrite());
    }
    Check(cudssMatrixSetValues(impl->matrix, impl->effective_mixed ? pack_mixed()
        : const_cast<double *>((keep_upper ? impl->upper_values : impl->values).Read())));
    Sync();
    const auto factor_begin = std::chrono::steady_clock::now();
    Check(cudssExecute(impl->handle, CUDSS_PHASE_FACTORIZATION, impl->config, impl->data,
                      impl->matrix, impl->solution_matrix, impl->rhs_matrix),
          "factorization with reused analysis");
    Sync();
    int info = 0;
    size_t written = 0;
    Check(cudssDataGet(impl->handle, impl->data, CUDSS_DATA_INFO, &info, sizeof(info), &written));
    MFEM_VERIFY(written == sizeof(info), "Invalid cuDSS refactorization info!");
    if (info != 0 && impl->effective_mixed) impl->Recover("fp32_refactorization_info");
    else MFEM_VERIFY(info == 0, "Native complex cuDSS refactorization device error: " << info);
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
  if (keep_upper)
  {
    impl->upper_offsets.SetSize(n + 1);
    impl->upper_columns.SetSize(int(upper_columns.size()));
    std::copy(upper_offsets.begin(), upper_offsets.end(), impl->upper_offsets.HostWrite());
    std::copy(upper_columns.begin(), upper_columns.end(), impl->upper_columns.HostWrite());
  }
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
  if (impl->mixed) impl->residual.SetSize(2 * n);
  Check(cudssCreate(&impl->handle));
  Check(cudssConfigCreate(&impl->config));
  {
    size_t written = 0;
    Check(cudssConfigGet(impl->config, CUDSS_CONFIG_IR_N_STEPS,
                        &impl->fp64_refinement, sizeof(impl->fp64_refinement), &written));
    MFEM_VERIFY(written == sizeof(impl->fp64_refinement), "Invalid FP64 refinement query!");
  }
  ConfigureThreading(impl->handle, impl->config);
  Check(cudssDataCreate(impl->handle, &impl->data));
  ConfigureTuning(impl->config);
  const auto dtype = impl->effective_mixed ? CUDA_C_32F : CUDA_C_64F;
  void *matrix_values = const_cast<double *>(impl->values.Read());
  void *rhs_values = impl->rhs.Write(), *solution_values = impl->solution.Write();
  if (keep_upper && !impl->effective_mixed)
  {
    impl->upper_values.SetSize(int(upper_values.size()));
    std::copy(upper_values.begin(), upper_values.end(), impl->upper_values.HostWrite());
    matrix_values = const_cast<double *>(impl->upper_values.Read());
  }
  if (impl->effective_mixed)
  {
    // Built-in same-dtype refinement is explicitly disabled: all corrections below
    // use the original FP64 CSR. A fixed count preserves the chosen PC structure.
    int refinement = 0;
    Check(cudssConfigSet(impl->config, CUDSS_CONFIG_IR_N_STEPS, &refinement, sizeof(refinement)));
    impl->float_rhs.SetSize(n);
    impl->float_solution.SetSize(n);
    impl->residual.SetSize(2*n);
    impl->invalid.SetSize(1);
    matrix_values = pack_mixed();
    rhs_values = impl->float_rhs.Write();
    solution_values = impl->float_solution.Write();
  }
  // A complex-symmetric Maxwell matrix is not Hermitian: SYMMETRIC (LDL^T), never HERMITIAN.
  const auto &solver_offsets = keep_upper ? impl->upper_offsets : impl->offsets;
  const auto &solver_columns = keep_upper ? impl->upper_columns : impl->columns;
  Check(cudssMatrixCreateCsr(&impl->matrix, n, n, solver_columns.Size(),
                            const_cast<int *>(solver_offsets.Read()), nullptr,
                            const_cast<int *>(solver_columns.Read()),
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
  MFEM_VERIFY(written == sizeof(info), "Invalid cuDSS factorization info!");
  if (info != 0 && impl->effective_mixed) impl->Recover("fp32_factorization_info");
  else MFEM_VERIFY(info == 0, "Native complex cuDSS factorization device error: " << info);
  height = width = n;
  Mpi::Print("PALACE_NATIVE_COMPLEX_COARSE: dimension={} nnz={} dtype={} matrix={}\n",
             n, impl->columns.Size(), impl->effective_mixed ? "complex_fp32" : "complex_fp64",
             impl->symmetric ? "symmetric_upper" : "general");
  Mpi::Print("PALACE_NATIVE_COARSE_PRECISION: requestedprecision={} effectiveprecision={} fallback_reason={}\n",
             impl->mixed ? "fp32" : "fp64",
             impl->effective_mixed ? "fp32_factors_fp64_corrections" : "fp64", impl->fallback_reason);
}

void ComplexCuDSSSolver::Mult(const ComplexVector &x, ComplexVector &y) const
{
  MFEM_VERIFY(impl->handle && x.Size() == width && y.Size() == height,
              "Uninitialized or mismatched native complex coarse solve!");
  x.Get(reinterpret_cast<std::complex<double> *>(impl->rhs.Write()), width, true);
  if (impl->effective_mixed)
  {
    const auto *b = reinterpret_cast<const cuDoubleComplex *>(impl->rhs.Read());
    auto *s = reinterpret_cast<cuDoubleComplex *>(impl->solution.Write());
    // Fixed correction count while mixed is healthy; failed applies recover once.
    bool conversion_failed = false;
    for (int step = 0; step <= impl->corrections; ++step)
    {
      auto *r = reinterpret_cast<cuDoubleComplex *>(impl->residual.Write());
      if (step) CheckCuda(mixedcoarse::Residual(width, 1, impl->offsets.Read(), impl->columns.Read(),
          reinterpret_cast<const cuDoubleComplex *>(impl->values.Read()), s, b, r));
      CheckCuda(cudaMemset(impl->invalid.Write(), 0, sizeof(int)));
      CheckCuda(mixedcoarse::Pack(width, 1, impl->scale.Read(), step ? r : b,
          impl->float_rhs.Write(), nullptr, impl->invalid.Write()));
      Sync();
      if (impl->invalid.HostRead()[0] != 0)
      {
        conversion_failed = true;
        break;
      }
      Check(cudssExecute(impl->handle, CUDSS_PHASE_SOLVE, impl->config, impl->data,
          impl->matrix, impl->solution_matrix, impl->rhs_matrix), "FP32 solve/correction");
      CheckCuda(mixedcoarse::Accumulate(width, 1, impl->scale.Read(), impl->float_solution.Read(), s, step != 0));
      Sync();
    }
    double rn = std::numeric_limits<double>::infinity(), bn = 0.0;
    if (!conversion_failed)
    {
      CheckCuda(mixedcoarse::Residual(width, 1, impl->offsets.Read(), impl->columns.Read(),
          reinterpret_cast<const cuDoubleComplex *>(impl->values.Read()), s, b,
          reinterpret_cast<cuDoubleComplex *>(impl->residual.Write())));
      Sync();
      rn = linalg::Norml2(impl->comm, impl->residual);
      bn = linalg::Norml2(impl->comm, impl->rhs);
    }
    const double relative = bn > 0.0 ? rn / bn : rn;
    if (!conversion_failed && std::isfinite(rn) && std::isfinite(bn) &&
        std::isfinite(relative) && relative <= 1e-3)
    {
      impl->max_residual = std::max(impl->max_residual, relative);
      ++impl->solves;
      ++impl->generation_solves;
      y.Set(reinterpret_cast<const std::complex<double> *>(impl->solution.Read()), height, true);
      Sync();
      return;
    }
    Mpi::Print("PALACE_NATIVE_MIXED_FAILED: relative_residual={:.9e} gate=1e-3\n", relative);
    MFEM_VERIFY(impl->generation_solves == 0,
                "Native mixed coarse failed after a successful PC apply; restart-needed: "
                "restart this operator solve with PALACE_NATIVE_COARSE_FP32=0. No PC switch performed!");
    impl->Recover(conversion_failed ? "rhs_conversion" : "original_fp64_residual");
  }
  Check(cudssMatrixSetValues(impl->rhs_matrix, impl->rhs.Write()));
  Check(cudssMatrixSetValues(impl->solution_matrix, impl->solution.Write()));
  Sync();
  Check(cudssExecute(impl->handle, CUDSS_PHASE_SOLVE, impl->config, impl->data,
                    impl->matrix, impl->solution_matrix, impl->rhs_matrix));
  Sync();
  if (impl->mixed)
  {
    CheckCuda(mixedcoarse::Residual(width, 1, impl->offsets.Read(), impl->columns.Read(),
        reinterpret_cast<const cuDoubleComplex *>(impl->values.Read()),
        reinterpret_cast<const cuDoubleComplex *>(impl->solution.Read()),
        reinterpret_cast<const cuDoubleComplex *>(impl->rhs.Read()),
        reinterpret_cast<cuDoubleComplex *>(impl->residual.Write())));
    Sync();
    const double rn = linalg::Norml2(impl->comm, impl->residual), bn = linalg::Norml2(impl->comm, impl->rhs);
    const double relative = bn > 0.0 ? rn / bn : rn;
    if ((!std::isfinite(relative) || relative > 1e-3) && width <= 4)
    {
      const auto *bv = impl->rhs.HostRead(), *sv = impl->solution.HostRead();
      for (int i = 0; i < width; ++i)
        Mpi::Print("PALACE_NATIVE_RECOVERY_DIAG: row={} b=({:.17e},{:.17e}) solution=({:.17e},{:.17e})\n",
                   i, bv[2*i], bv[2*i+1], sv[2*i], sv[2*i+1]);
      const auto *av = impl->upper_values.HostRead();
      for (int j = 0; impl->symmetric && j < impl->upper_columns.Size(); ++j)
        Mpi::Print("PALACE_NATIVE_RECOVERY_DIAG: upper_entry={} value=({:.17e},{:.17e})\n",
                   j, av[2*j], av[2*j+1]);
    }
    MFEM_VERIFY(std::isfinite(relative) && relative <= 1e-3, "FP64 recovered coarse residual failed: " << relative);
  }
  y.Set(reinterpret_cast<const std::complex<double> *>(impl->solution.Read()), height, true);
  Sync();
}

}  // namespace palace

#endif
