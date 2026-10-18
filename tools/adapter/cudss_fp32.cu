// Experimental single-rank cuDSS FP32 preconditioner for an otherwise FP64 Palace.
// Interpose only the public matrix/execute API; leave Palace/MFEM binaries immutable.
#include <cudss.h>
#include <cuda_runtime.h>
#include <nvtx3/nvToolsExt.h>
#include <dlfcn.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <limits>
#include <string_view>
#include <unordered_map>

namespace {
struct Matrix { int64_t count; void *original; float *values; bool csr; };
std::unordered_map<cudssMatrix_t, Matrix> matrices;
std::unordered_map<cudssHandle_t, cudaStream_t> streams;
uint64_t allocated = 0, peak = 0, factors = 0, solves = 0;
template <typename T> T next(const char *name) {
  void *p = dlsym(RTLD_NEXT, name);
  if (!p) { std::fprintf(stderr, "FP32 shim: missing %s\n", name); std::abort(); }
  return reinterpret_cast<T>(p);
}
bool enabled() {
  static const bool value = [] {
    const char *p = std::getenv("PALACE_CUDSS_FP32");
    if (!p || std::string_view(p) != "1") return false;
    const char *ranks = std::getenv("OMPI_COMM_WORLD_SIZE");
    if (ranks && std::string_view(ranks) != "1") {
      std::fprintf(stderr, "FP32 shim supports one MPI rank only\n"); std::abort();
    }
    return true;
  }();
  return value;
}
template <typename In, typename Out>
__global__ void convert(const In *in, Out *out, int64_t n) {
  for (int64_t i = blockIdx.x * int64_t(blockDim.x) + threadIdx.x;
       i < n; i += int64_t(blockDim.x) * gridDim.x) out[i] = static_cast<Out>(in[i]);
}
cudssStatus_t allocate(int64_t n, float **p) {
  if (n < 0 || uint64_t(n) > std::numeric_limits<size_t>::max() / sizeof(float))
    return CUDSS_STATUS_INVALID_VALUE;
  if (n && cudaMalloc(reinterpret_cast<void **>(p), size_t(n) * sizeof(float)) != cudaSuccess)
    return CUDSS_STATUS_ALLOC_FAILED;
  allocated += size_t(n) * sizeof(float); if (allocated > peak) peak = allocated;
  return CUDSS_STATUS_SUCCESS;
}
void release(Matrix &m) {
  if (m.values) cudaFree(m.values);
  allocated -= size_t(m.count) * sizeof(float);
}
cudssStatus_t down(Matrix &m, cudaStream_t stream) {
  if (!m.original || !m.values) return CUDSS_STATUS_INVALID_VALUE;
  if (m.count) convert<<<256,256,0,stream>>>(static_cast<const double *>(m.original), m.values, m.count);
  return cudaGetLastError() == cudaSuccess ? CUDSS_STATUS_SUCCESS : CUDSS_STATUS_EXECUTION_FAILED;
}
__attribute__((destructor)) void report() {
  if (factors || solves) std::fprintf(stderr,
    "CUDSS_FP32: factors=%llu solves=%llu peak_conversion_bytes=%llu live_conversion_bytes=%llu; outer_FEM_Krylov_FP64\n",
    (unsigned long long)factors, (unsigned long long)solves,
    (unsigned long long)peak, (unsigned long long)allocated);

}
}

extern "C" cudssStatus_t cudssSetStream(cudssHandle_t h, cudaStream_t s) {
  static auto fn = next<decltype(&cudssSetStream)>("cudssSetStream");
  auto status = fn(h,s); if (status == CUDSS_STATUS_SUCCESS) streams[h] = s; return status;
}
extern "C" cudssStatus_t cudssDestroy(cudssHandle_t h) {
  static auto fn = next<decltype(&cudssDestroy)>("cudssDestroy");
  auto status = fn(h); if (status == CUDSS_STATUS_SUCCESS) streams.erase(h); return status;
}
extern "C" cudssStatus_t cudssMatrixCreateCsr(cudssMatrix_t *m, int64_t rows,
    int64_t cols, int64_t nnz, void *start, void *end, void *indices, void *values,
    cudaDataType_t index_type, cudaDataType_t value_type, cudssMatrixType_t type,
    cudssMatrixViewType_t view, cudssIndexBase_t base) {
  static auto fn = next<decltype(&cudssMatrixCreateCsr)>("cudssMatrixCreateCsr");
  if (!enabled()) return fn(m,rows,cols,nnz,start,end,indices,values,index_type,value_type,type,view,base);
  if (value_type != CUDA_R_64F) return CUDSS_STATUS_NOT_SUPPORTED;
  Matrix data{nnz,values,nullptr,true}; auto status = allocate(nnz,&data.values);
  if (status != CUDSS_STATUS_SUCCESS) return status;
  status = fn(m,rows,cols,nnz,start,end,indices,data.values,index_type,CUDA_R_32F,type,view,base);
  if (status == CUDSS_STATUS_SUCCESS) matrices.emplace(*m,data); else release(data);
  return status;
}
extern "C" cudssStatus_t cudssMatrixCreateDn(cudssMatrix_t *m, int64_t rows,
    int64_t cols, int64_t ld, void *values, cudaDataType_t type, cudssLayout_t layout) {
  static auto fn = next<decltype(&cudssMatrixCreateDn)>("cudssMatrixCreateDn");
  if (!enabled()) return fn(m,rows,cols,ld,values,type,layout);
  if (type != CUDA_R_64F || layout != CUDSS_LAYOUT_COL_MAJOR || rows < 0 || cols < 0 ||
      ld < rows || (cols && ld > std::numeric_limits<int64_t>::max()/cols))
    return CUDSS_STATUS_NOT_SUPPORTED;
  Matrix data{ld*cols,values,nullptr,false}; auto status = allocate(data.count,&data.values);
  if (status != CUDSS_STATUS_SUCCESS) return status;
  status = fn(m,rows,cols,ld,data.values,CUDA_R_32F,layout);
  if (status == CUDSS_STATUS_SUCCESS) matrices.emplace(*m,data); else release(data);
  return status;
}
extern "C" cudssStatus_t cudssMatrixSetValues(cudssMatrix_t m, void *values) {
  static auto fn = next<decltype(&cudssMatrixSetValues)>("cudssMatrixSetValues");
  auto it = matrices.find(m);
  if (it == matrices.end()) return fn(m,values);
  it->second.original = values; return fn(m,it->second.values);
}
extern "C" cudssStatus_t cudssMatrixDestroy(cudssMatrix_t m) {
  static auto fn = next<decltype(&cudssMatrixDestroy)>("cudssMatrixDestroy");
  auto status = fn(m);
  auto it = matrices.find(m);
  if (status == CUDSS_STATUS_SUCCESS && it != matrices.end()) {
    release(it->second); matrices.erase(it);
  }
  return status;
}
extern "C" cudssStatus_t cudssExecute(cudssHandle_t h, int phase, cudssConfig_t config,
    cudssData_t data, cudssMatrix_t a, cudssMatrix_t x, cudssMatrix_t b) {
  static auto fn = next<decltype(&cudssExecute)>("cudssExecute");
  if (!enabled()) return fn(h,phase,config,data,a,x,b);
  auto ai = matrices.find(a), xi = matrices.find(x), bi = matrices.find(b);
  if (ai == matrices.end() || xi == matrices.end() || bi == matrices.end())
    return CUDSS_STATUS_NOT_SUPPORTED;
  const auto stream = streams[h];
  // MFEM uses the default stream. Honor an explicitly selected cuDSS stream too.
  if (phase & (CUDSS_PHASE_ANALYSIS | CUDSS_PHASE_FACTORIZATION | CUDSS_PHASE_REFACTORIZATION)) {
    auto status = down(ai->second,stream); if (status != CUDSS_STATUS_SUCCESS) return status;
  }
  const bool solve = (phase & CUDSS_PHASE_SOLVE) != 0;
  if (solve) {
    if (!xi->second.original) return CUDSS_STATUS_INVALID_VALUE;
    auto status = down(bi->second,stream); if (status != CUDSS_STATUS_SUCCESS) return status;
  }
  const bool factor = (phase & (CUDSS_PHASE_FACTORIZATION | CUDSS_PHASE_REFACTORIZATION)) != 0;
  if (factor) nvtxRangePushA("cudss_fp32_factor");
  auto status = fn(h,phase,config,data,a,x,b);
  if (factor) nvtxRangePop();
  if (status != CUDSS_STATUS_SUCCESS) return status;
  if (factor && std::getenv("PALACE_FP32_COLD_CSR")) {
    // The original double CSR values are only needed again for refactorization.
    // The FP32 cuDSS matrix/factors retain their own buffers. Move this cold
    // duplicate to host memory to leave more VRAM for repeated operator/solve work.
    auto &matrix = ai->second;
    cudaPointerAttributes attributes{};
    if (cudaPointerGetAttributes(&attributes,matrix.original)!=cudaSuccess ||
        attributes.type!=cudaMemoryTypeManaged) {
      std::fprintf(stderr,"FP32 cold CSR requires a managed original matrix\n");
      return CUDSS_STATUS_NOT_SUPPORTED;
    }
    size_t bytes=size_t(matrix.count)*sizeof(double);
    auto error=cudaMemAdvise(matrix.original,bytes,cudaMemAdviseSetPreferredLocation,cudaCpuDeviceId);
    if(error==cudaSuccess)error=cudaMemPrefetchAsync(matrix.original,bytes,cudaCpuDeviceId,stream);
    if(error!=cudaSuccess)return CUDSS_STATUS_EXECUTION_FAILED;
    std::fprintf(stderr,"FP32_COLD_CSR: host_preferred_original_bytes=%zu\n",bytes);
  }
  if (phase & (CUDSS_PHASE_FACTORIZATION | CUDSS_PHASE_REFACTORIZATION)) ++factors;
  if (solve) {
    convert<<<256,256,0,stream>>>(xi->second.values,static_cast<double *>(xi->second.original),xi->second.count);
    if (cudaGetLastError() != cudaSuccess) return CUDSS_STATUS_EXECUTION_FAILED;
    ++solves;
  }
  return status;
}
