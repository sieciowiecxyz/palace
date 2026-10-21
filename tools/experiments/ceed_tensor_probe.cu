// SPDX-License-Identifier: Apache-2.0
#include <cuda_runtime.h>
#include <cstddef>

__global__ void pack(const double *x, float *y, size_t n) {
  const size_t i=size_t(blockIdx.x)*blockDim.x+threadIdx.x;
  if(i<n)y[i]=float(x[i]);
}
__global__ void unpack(const float *x, double *y, size_t n, bool add) {
  const size_t i=size_t(blockIdx.x)*blockDim.x+threadIdx.x;
  if(i<n)y[i]=(add?y[i]:0.0)+double(x[i]);
}
extern "C" cudaError_t palace_probe_pack(const double *x,float *y,size_t n) {
  pack<<<(n+255)/256,256>>>(x,y,n);return cudaGetLastError();
}
extern "C" cudaError_t palace_probe_unpack(const float *x,double *y,size_t n,bool add) {
  unpack<<<(n+255)/256,256>>>(x,y,n,add);return cudaGetLastError();
}

#include "../adapter/ceed_fused.cuh"
extern "C" cudaError_t palace_probe_fused_basis(const float *b,const double *x,double *y,
                                                int p,int q,int qc,int n,bool trans,bool add) {
  return palace_pc_basis::Apply(b,x,y,p,q,qc,n,trans,add);
}
