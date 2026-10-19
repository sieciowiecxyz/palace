// SPDX-License-Identifier: Apache-2.0
// Isolated arithmetic/traffic probe, not a Palace solve or HYPRE benchmark.
#include <cuda_runtime.h>
#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
#include "linalg/mixedbasis.hpp"

namespace
{
using palace::mixed_basis::Pair;
thread_local std::string error;
void check(cudaError_t code)
{
  if (code != cudaSuccess) throw std::runtime_error(cudaGetErrorString(code));
}
struct Buffer
{
  void *data = nullptr;
  explicit Buffer(std::size_t bytes) { check(cudaMalloc(&data, bytes)); }
  ~Buffer() { cudaFree(data); }
  template <class T> T *as() { return static_cast<T *>(data); }
};
struct Event
{
  cudaEvent_t event;
  Event() { check(cudaEventCreate(&event)); }
  ~Event() { cudaEventDestroy(event); }
};

__global__ void pack(int n, const double *br, const double *bi, float *pr, float *pi)
{
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < n) { pr[i] = static_cast<float>(br[i]); pi[i] = static_cast<float>(bi[i]); }
}
__global__ void unpack(int n, const float *pr, const float *pi, double *br, double *bi)
{
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < n) { br[i] = static_cast<double>(pr[i]); bi[i] = static_cast<double>(pi[i]); }
}
template <class Storage>
__global__ void dot(int n, int parts, const Storage *br, const Storage *bi,
                    const double *wr, const double *wi, Pair *partial)
{
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < parts) partial[i] = palace::mixed_basis::DotPart(i, parts, n, br, bi, wr, wi);
}
__global__ void reduce(int parts, const Pair *partial, Pair *result)
{
  __shared__ Pair values[256];
  Pair value{0.0, 0.0};
  for (int i = threadIdx.x; i < parts; i += blockDim.x)
  { value.real += partial[i].real; value.imag += partial[i].imag; }
  values[threadIdx.x] = value; __syncthreads();
  for (int d = blockDim.x / 2; d; d /= 2)
  {
    if (threadIdx.x < d)
    { values[threadIdx.x].real += values[threadIdx.x+d].real;
      values[threadIdx.x].imag += values[threadIdx.x+d].imag; }
    __syncthreads();
  }
  if (threadIdx.x == 0) *result = values[0];
}
template <class Storage>
__global__ void add(int n, const Storage *br, const Storage *bi,
                    double ar, double ai, double *wr, double *wi)
{
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < n) palace::mixed_basis::AddEntry(i, br, bi, ar, ai, wr, wi);
}
}

extern "C" const char *mixed_basis_error() { return error.c_str(); }

extern "C" int mixed_basis_probe(int n, const double *br, const double *bi,
                                  const double *wr, const double *wi,
                                  double ar, double ai, int repeats, int reverse_order,
                                  double *dots, double *direct_r, double *direct_i,
                                  double *baseline_r, double *baseline_i,
                                  double *times_ms, std::uint64_t *bytes)
{
  try
  {
    if (n < 1 || n > (1<<22) || repeats < 1 || repeats > 100)
      throw std::runtime_error("Bounded positive vector length/repeats required");
    const int parts = std::min(n, 65536), blocks = (n+255)/256;
    const auto dbytes = std::size_t(n)*sizeof(double), fbytes = std::size_t(n)*sizeof(float);
    Buffer original_r(dbytes), original_i(dbytes), packed_r(fbytes), packed_i(fbytes);
    Buffer input_r(dbytes), input_i(dbytes), work_r(dbytes), work_i(dbytes);
    Buffer unpacked_r(dbytes), unpacked_i(dbytes), partial(parts*sizeof(Pair)), result(sizeof(Pair));
    for (auto entry : std::vector<std::pair<Buffer *,const double *>>{
           {&original_r,br},{&original_i,bi},{&input_r,wr},{&input_i,wi}})
      check(cudaMemcpy(entry.first->data,entry.second,dbytes,cudaMemcpyHostToDevice));
    pack<<<blocks,256>>>(n,original_r.as<double>(),original_i.as<double>(),packed_r.as<float>(),packed_i.as<float>());
    check(cudaGetLastError()); check(cudaDeviceSynchronize());
    auto run = [&](bool direct)
    {
      check(cudaMemcpy(work_r.data,input_r.data,dbytes,cudaMemcpyDeviceToDevice));
      check(cudaMemcpy(work_i.data,input_i.data,dbytes,cudaMemcpyDeviceToDevice));
      if (direct)
        dot<<<(parts+255)/256,256>>>(n,parts,packed_r.as<float>(),packed_i.as<float>(),work_r.as<double>(),work_i.as<double>(),partial.as<Pair>());
      else
      {
        unpack<<<blocks,256>>>(n,packed_r.as<float>(),packed_i.as<float>(),unpacked_r.as<double>(),unpacked_i.as<double>());
        dot<<<(parts+255)/256,256>>>(n,parts,unpacked_r.as<double>(),unpacked_i.as<double>(),work_r.as<double>(),work_i.as<double>(),partial.as<Pair>());
      }
      reduce<<<1,256>>>(parts,partial.as<Pair>(),result.as<Pair>());
      if (direct) add<<<blocks,256>>>(n,packed_r.as<float>(),packed_i.as<float>(),ar,ai,work_r.as<double>(),work_i.as<double>());
      else add<<<blocks,256>>>(n,unpacked_r.as<double>(),unpacked_i.as<double>(),ar,ai,work_r.as<double>(),work_i.as<double>());
      check(cudaGetLastError());
    };
    for (int trial=0;trial<2;trial++)
    {
      const int mode=reverse_order ? 1-trial : trial;
      const bool direct=mode==0;
      run(direct);run(direct);check(cudaDeviceSynchronize());
      Event begin,end;check(cudaEventRecord(begin.event));
      for (int j=0;j<repeats;j++) run(direct);
      check(cudaEventRecord(end.event));check(cudaEventSynchronize(end.event));
      float elapsed;check(cudaEventElapsedTime(&elapsed,begin.event,end.event));
      times_ms[mode]=elapsed/repeats;
      check(cudaMemcpy(dots+mode*2,result.data,sizeof(Pair),cudaMemcpyDeviceToHost));
      check(cudaMemcpy(direct?direct_r:baseline_r,work_r.data,dbytes,cudaMemcpyDeviceToHost));
      check(cudaMemcpy(direct?direct_i:baseline_i,work_i.data,dbytes,cudaMemcpyDeviceToHost));
    }
    bytes[0]=8*dbytes+2*fbytes+parts*sizeof(Pair)+sizeof(Pair); // shared-process explicit allocations
    bytes[1]=parts*sizeof(Pair)+sizeof(Pair); // algorithm reduction workspace
    bytes[2]=2*dbytes; // unpack buffer needed by the baseline only
    error.clear();return 0;
  }
  catch (const std::exception &exception) { error=exception.what();return 1; }
}
