// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <cuda_runtime.h>
#include <cstddef>

namespace palace_compensated {
// FMA product residual + TwoSum accumulation. Explicit rounding intrinsics
// protect the error-free addition transform from compiler reassociation.
__device__ inline void add_product(float ah,float al,float xh,float xl,float &sum,float &low) {
  const float product=__fmul_rn(ah,xh);
  float error=fmaf(ah,xh,-product);
  error=fmaf(ah,xl,error);error=fmaf(al,xh,error);error=fmaf(al,xl,error);
  const float next=__fadd_rn(sum,product),v=__fsub_rn(next,sum);
  const float residual=__fadd_rn(__fsub_rn(sum,__fsub_rn(next,v)),__fsub_rn(product,v));
  low=__fadd_rn(low,__fadd_rn(residual,error));sum=next;
}

template<int P,int Q,int QC,bool Bits>
__global__ void forward(const float *hi,const float *lo,const double *x,double *y,int n) {
  const size_t i=size_t(blockIdx.x)*blockDim.x+threadIdx.x;
  if(i>=size_t(n)*Q)return;
  const size_t e=i/Q;const int q=i%Q;
  float sum[QC]={},low[QC]={};double rare[QC]={};bool has_rare=false;
#pragma unroll
  for(int p=0;p<P;++p){const double value=x[e*P+p];float xh,xl;
    if constexpr(Bits){
      const auto bits=static_cast<unsigned long long>(__double_as_longlong(value));
      const int exponent=int((bits>>52)&2047);
      if((bits&0x7fffffffffffffffULL)==0){xh=0;xl=0;}
      else if(exponent>=949&&exponent<=1123){
        // RZ retains the first 24 significand bits; the remaining 29 bits
        // have weight 2^(E-52). Avoid a per-input FP64 subtraction on SM120.
        xh=__double2float_rz(value);
        const unsigned tail=unsigned(bits&((1ULL<<29)-1));
        const float weight=__int_as_float((exponent-948)<<23);
        xl=copysignf(__fmul_rn(__uint2float_rn(tail),weight),xh);
      }else{
        // Out-of-range values are not silently flushed/overflowed to FP32.
        // This is an experimental fallback, not a pure FP32 implementation.
        has_rare=true;
#pragma unroll
        for(int d=0;d<QC;++d){const int j=d*P*Q+q*P+p;
          rare[d]=fma(double(hi[j])+double(lo[j]),value,rare[d]);}
        continue;
      }
    }else{xh=float(value);xl=float(value-double(xh));}
#pragma unroll
    for(int d=0;d<QC;++d){const int j=d*P*Q+q*P+p;add_product(hi[j],lo[j],xh,xl,sum[d],low[d]);}}
#pragma unroll
  for(int d=0;d<QC;++d){double value=double(sum[d])+double(low[d]);
    if constexpr(Bits){if(has_rare)value+=rare[d];}y[size_t(d)*n*Q+i]=value;}
}

template<bool Bits=false>
inline cudaError_t Apply(const float *hi,const float *lo,const double *x,double *y,int p,int q,int qc,int n) {
  if(!hi||!lo||!x||!y||n<=0||p<=0||p>40||q<=0||q>40||qc<=0||qc>3
      ||static_cast<long long>(n)*q*qc>2147483647LL||static_cast<long long>(n)*p>2147483647LL)return cudaErrorInvalidValue;
#define SHAPE(P,Q,C) if(p==P&&q==Q&&qc==C){forward<P,Q,C,Bits><<<(size_t(n)*Q+255)/256,256>>>(hi,lo,x,y,n);return cudaGetLastError();}
  SHAPE(20,14,3) SHAPE(20,6,3)
  SHAPE(15,14,3) SHAPE(15,14,1) SHAPE(15,6,3) SHAPE(15,6,1)
  SHAPE(10,14,3) SHAPE(10,14,1) SHAPE(10,6,3) SHAPE(10,6,1)
  SHAPE(8,6,2) SHAPE(8,6,1)
#undef SHAPE
  return cudaErrorNotSupported;
}
}
