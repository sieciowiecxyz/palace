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

// FP64 caller storage, FP32 register arithmetic; no intermediate vector buffers.
// Templates specialize dimensions, not geometry/materials/frequencies.
template<int P,int Q,int QC,bool TRANSPOSE,bool ADD>
__global__ void fused_basis(const float *b,const double *x,double *y,int n) {
  const size_t i=size_t(blockIdx.x)*blockDim.x+threadIdx.x;
  if constexpr(!TRANSPOSE) {
    if(i>=size_t(n)*Q)return;
    const size_t e=i/Q;const int q=i%Q;
    float sum[QC]={};
#pragma unroll
    for(int p=0;p<P;++p){const float u=float(x[e*P+p]);
#pragma unroll
      for(int d=0;d<QC;++d)sum[d]=fmaf(b[d*P*Q+q*P+p],u,sum[d]);}
#pragma unroll
    for(int d=0;d<QC;++d)y[size_t(d)*n*Q+i]=double(sum[d]);
  } else {
    if(i>=size_t(n)*P)return;
    const size_t e=i/P;const int p=i%P;float sum=0;
#pragma unroll
    for(int d=0;d<QC;++d) {
#pragma unroll
      for(int q=0;q<Q;++q)sum=fmaf(b[d*P*Q+q*P+p],float(x[size_t(d)*n*Q+e*Q+q]),sum);
    }
    y[i]=(ADD?y[i]:0.0)+double(sum);
  }
}

template<int P,int Q,int QC> void launch_fused(const float *b,const double *x,double *y,int n,bool trans,bool add) {
  const size_t count=size_t(n)*(trans?P:Q);const unsigned blocks=(count+255)/256;
  if(!trans)fused_basis<P,Q,QC,false,false><<<blocks,256>>>(b,x,y,n);
  else if(add)fused_basis<P,Q,QC,true,true><<<blocks,256>>>(b,x,y,n);
  else fused_basis<P,Q,QC,true,false><<<blocks,256>>>(b,x,y,n);
}

extern "C" cudaError_t palace_probe_fused_basis(const float *b,const double *x,double *y,
                                                int p,int q,int qc,int n,bool trans,bool add) {
  if(!b||!x||!y||n<=0||p<=0||p>40||q<=0||q>40||qc<=0||qc>3||(add&&!trans)
     ||static_cast<long long>(n)*q*qc>2147483647LL
     ||static_cast<long long>(n)*p>2147483647LL)return cudaErrorInvalidValue;
#define SHAPE(P,Q,C) if(p==P&&q==Q&&qc==C){launch_fused<P,Q,C>(b,x,y,n,trans,add);return cudaGetLastError();}
  SHAPE(20,14,3) SHAPE(20,6,3)
  SHAPE(15,14,3) SHAPE(15,14,1) SHAPE(15,6,3) SHAPE(15,6,1)
  SHAPE(10,14,3) SHAPE(10,14,1) SHAPE(10,6,3) SHAPE(10,6,1)
  SHAPE(8,6,2) SHAPE(8,6,1)
#undef SHAPE
  return cudaErrorNotSupported;
}
