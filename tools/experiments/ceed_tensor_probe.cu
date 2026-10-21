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
#include "../adapter/ceed_compensated.cuh"
extern "C" cudaError_t palace_probe_fused_basis(const float *b,const double *x,double *y,
                                                int p,int q,int qc,int n,bool trans,bool add) {
  return palace_pc_basis::Apply(b,x,y,p,q,qc,n,trans,add);
}
extern "C" cudaError_t palace_probe_compensated(const float *hi,const float *lo,const double *x,double *y,int p,int q,int qc,int n) {
  return palace_compensated::Apply(hi,lo,x,y,p,q,qc,n);
}
extern "C" cudaError_t palace_probe_compensated_bits(const float *hi,const float *lo,const double *x,double *y,int p,int q,int qc,int n) {
  return palace_compensated::Apply<true>(hi,lo,x,y,p,q,qc,n);
}

#include <mma.h>
// Generic basis dimensions P20/Q14/QC3; no antenna geometry/material assumptions.
// Four warps each evaluate sixteen elements. All lanes execute every MMA.
__global__ void palace_probe_wmma_forward(const float *basis,const double *x,double *y,int n) {
  using namespace nvcuda;
  __shared__ __align__(32) float a[3*16*32],b[32*64],c[16*64];
  const int lane=threadIdx.x,warp=lane/32,first=blockIdx.x*64;
  for(int i=lane;i<3*16*32;i+=128){const int d=i/(16*32),q=(i/32)%16,k=i%32;
    a[i]=(q<14&&k<20)?wmma::__float_to_tf32(basis[d*20*14+q*20+k]):0.f;}
  for(int i=lane;i<32*64;i+=128){const int e=first+i/32,k=i%32;
    b[i]=(e<n&&k<20)?wmma::__float_to_tf32(float(x[size_t(e)*20+k])):0.f;}
  __syncthreads();
#pragma unroll
  for(int d=0;d<3;++d){
    wmma::fragment<wmma::accumulator,16,16,8,float> accum;
    wmma::fill_fragment(accum,0.f);
#pragma unroll
    for(int k=0;k<32;k+=8){
      wmma::fragment<wmma::matrix_a,16,16,8,wmma::precision::tf32,wmma::row_major> af;
      wmma::fragment<wmma::matrix_b,16,16,8,wmma::precision::tf32,wmma::col_major> bf;
      wmma::load_matrix_sync(af,a+d*16*32+k,32);
      wmma::load_matrix_sync(bf,b+warp*16*32+k,32);
      wmma::mma_sync(accum,af,bf,accum);
    }
    wmma::store_matrix_sync(c+warp*16*16,accum,16,wmma::mem_col_major);
    __syncthreads();
    for(int i=lane;i<16*64;i+=128){const int e=first+i/16,q=i%16;
      if(e<n&&q<14)y[size_t(d)*n*14+size_t(e)*14+q]=double(c[i]);}
    __syncthreads();
  }
}
extern "C" cudaError_t palace_probe_wmma(const float *basis,const double *x,double *y,int p,int q,int qc,int n) {
  if(!basis||!x||!y||n<=0||static_cast<long long>(n)*42>2147483647LL)return cudaErrorInvalidValue;
  if(p!=20||q!=14||qc!=3)return cudaErrorNotSupported;
  palace_probe_wmma_forward<<<(n+63)/64,128>>>(basis,x,y,n);return cudaGetLastError();
}
