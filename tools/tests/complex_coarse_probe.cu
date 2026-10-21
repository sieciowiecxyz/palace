// SPDX-License-Identifier: Apache-2.0
// Same manufactured non-Hermitian complex system in native and real-block FP64.
#include <cudss.h>
#include <cuda_runtime.h>
#include <cuComplex.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <complex>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <string>
#include <map>
#include <stdexcept>
#include <type_traits>
#include <vector>

#define CUDA(call) do { auto e=(call); if(e!=cudaSuccess) throw std::runtime_error(cudaGetErrorString(e)); } while(0)
#define DSS(call) do { auto e=(call); if(e!=CUDSS_STATUS_SUCCESS) { std::fprintf(stderr,"%s: cuDSS code %d\n",#call,int(e)); throw std::runtime_error("cuDSS failed"); } } while(0)
using Complex = std::complex<double>;
using Clock = std::chrono::steady_clock;

struct Allocation {
  bool hybrid=false;
  std::atomic<size_t> live{0}, peak{0};
  static int alloc(void *ctx, void **p, size_t n, cudaStream_t) {
    *p=nullptr;
    if(!n) return 0;
    auto &self=*static_cast<Allocation *>(ctx);
    auto error=self.hybrid?cudaMalloc(p,n):cudaMallocManaged(p,n,cudaMemAttachGlobal);
    if(error!=cudaSuccess) return 1;
    size_t current=self.live.fetch_add(n)+n, previous=self.peak.load();
    while(previous<current && !self.peak.compare_exchange_weak(previous,current)) {}
    return 0;
  }
  static int free(void *ctx, void *p, size_t n, cudaStream_t) {
    if(cudaFree(p)!=cudaSuccess) return 1;
    if(p) static_cast<Allocation *>(ctx)->live.fetch_sub(n);
    return 0;
  }
};

template <typename T> struct Buffer {
  T *p=nullptr;
  explicit Buffer(size_t n) { CUDA(cudaMallocManaged(reinterpret_cast<void **>(&p),n*sizeof(T))); }
  ~Buffer() { if(p) cudaFree(p); }
  Buffer(const Buffer &)=delete;
  Buffer &operator=(const Buffer &)=delete;
};

// Fixed sparse 3D stencil; imaginary part is nonzero and the matrix is NOT Hermitian.
std::vector<std::map<int,Complex>> matrix(int side, int update) {
  int n=side*side*side;
  std::vector<std::map<int,Complex>> rows(n);
  for(int z=0;z<side;++z) for(int y=0;y<side;++y) for(int x=0;x<side;++x) {
    int i=x+side*(y+side*z);
    rows[i][i]=Complex(-1.5+0.125*update,0.7+0.05*update);
    for(auto step:std::vector<int>{-1,1}) {
      if(x+step>=0 && x+step<side) rows[i][i+step]=Complex(-1,0.03);
      if(y+step>=0 && y+step<side) rows[i][i+step*side]=Complex(-1,0.03);
      if(z+step>=0 && z+step<side) rows[i][i+step*side*side]=Complex(-1,0.03);
    }
  }
  return rows;
}

template <typename T> void run_case(int side, int hybrid_mib) {
  constexpr bool native=std::is_same<T,cuDoubleComplex>::value;
  const int n=side*side*side, dim=native?n:2*n, nrhs=2;
  auto source=matrix(side,0);
  std::vector<int> offsets(dim+1), columns;
  std::vector<T> values;
  auto assemble=[&](int update) {
    source=matrix(side,update);
    columns.clear(); values.clear();
    for(int i=0;i<dim;++i) {
      offsets[i]=int(columns.size());
      std::map<int,Complex> row;
      for(auto [j,a]:source[i%n]) {
        if constexpr(native) row[j]=a;
        else { row[j]=i<n?a.real():a.imag(); row[j+n]=i<n?a.imag():-a.real(); }
      }
      for(auto [j,a]:row) {
        columns.push_back(j);
        if constexpr(native) values.push_back(make_cuDoubleComplex(a.real(),a.imag()));
        else values.push_back(a.real());
      }
    }
    offsets[dim]=int(columns.size());
  };
  assemble(0);
  Buffer<int> ri(offsets.size()), ci(columns.size());
  Buffer<T> av(values.size()), bv(dim*nrhs), xv(dim*nrhs);
  std::copy(offsets.begin(),offsets.end(),ri.p);
  std::copy(columns.begin(),columns.end(),ci.p);
  Allocation allocation;
  allocation.hybrid=hybrid_mib!=0;
  int64_t minimum_device_bytes=0, estimated_host_bytes=0;
  int64_t limit_bytes=int64_t(hybrid_mib)*1024*1024;
  cudssHandle_t handle; cudssConfig_t config; cudssData_t data; cudssMatrix_t a,b,x;
  DSS(cudssCreate(&handle));
  cudssDeviceMemHandler_t handler{};
  handler.ctx=&allocation; handler.device_alloc=Allocation::alloc; handler.device_free=Allocation::free;
  std::snprintf(handler.name,sizeof(handler.name),"probe RAM/VRAM");
  DSS(cudssSetDeviceMemHandler(handle,&handler));
  DSS(cudssConfigCreate(&config)); DSS(cudssDataCreate(handle,&data));
  if(hybrid_mib) {
    int mode=1;
    DSS(cudssConfigSet(config,CUDSS_CONFIG_HYBRID_MODE,&mode,sizeof(mode)));
    DSS(cudssConfigSet(config,CUDSS_CONFIG_HYBRID_DEVICE_MEMORY_LIMIT,&limit_bytes,sizeof(limit_bytes)));
  }

  auto dtype=native?CUDA_C_64F:CUDA_R_64F;
  DSS(cudssMatrixCreateCsr(&a,dim,dim,values.size(),ri.p,nullptr,ci.p,av.p,
                         CUDA_R_32I,dtype,native?CUDSS_MTYPE_GENERAL:CUDSS_MTYPE_SYMMETRIC,
                         CUDSS_MVIEW_FULL,CUDSS_BASE_ZERO));
  DSS(cudssMatrixCreateDn(&b,dim,nrhs,dim,bv.p,dtype,CUDSS_LAYOUT_COL_MAJOR));
  DSS(cudssMatrixCreateDn(&x,dim,nrhs,dim,xv.p,dtype,CUDSS_LAYOUT_COL_MAJOR));
  double error_max=0,residual_max=0,analysis_s=0,factor_s=0,solve_s=0;
  auto execute=[&](int phase) {
    CUDA(cudaDeviceSynchronize()); auto start=Clock::now();
    DSS(cudssExecute(handle,phase,config,data,a,x,b)); CUDA(cudaDeviceSynchronize());
    return std::chrono::duration<double>(Clock::now()-start).count();
  };
  for(int update=0;update<2;++update) {
    auto old_columns=columns; auto old_offsets=offsets;
    assemble(update);
    if(columns!=old_columns || offsets!=old_offsets) throw std::runtime_error("pattern changed");
    std::copy(values.begin(),values.end(),av.p);
    std::vector<Complex> exact(n*nrhs),rhs(n*nrhs),result(n*nrhs);
    for(int k=0;k<nrhs;++k) for(int i=0;i<n;++i)
      exact[k*n+i]=Complex(std::sin((i+1)*0.13+k),std::cos((i+1)*0.07-k));
    for(int k=0;k<nrhs;++k) for(int i=0;i<n;++i) {
      for(auto [j,v]:source[i]) rhs[k*n+i]+=v*exact[k*n+j];
      if constexpr(native) bv.p[k*dim+i]=make_cuDoubleComplex(rhs[k*n+i].real(),rhs[k*n+i].imag());
      else { bv.p[k*dim+i]=rhs[k*n+i].real(); bv.p[k*dim+i+n]=rhs[k*n+i].imag(); }
    }
    DSS(cudssMatrixSetValues(a,av.p)); DSS(cudssMatrixSetValues(b,bv.p)); DSS(cudssMatrixSetValues(x,xv.p));
    if(!update) {
      analysis_s=execute(CUDSS_PHASE_ANALYSIS);
      if(hybrid_mib) {
        size_t written=0;
        DSS(cudssDataGet(handle,data,CUDSS_DATA_HYBRID_DEVICE_MEMORY_MIN,
                        &minimum_device_bytes,sizeof(minimum_device_bytes),&written));
        if(written!=sizeof(minimum_device_bytes) || minimum_device_bytes<0 || minimum_device_bytes>limit_bytes)
          throw std::runtime_error("hybrid minimum exceeds explicit budget or invalid query");
        int64_t estimates[16]{};
        DSS(cudssDataGet(handle,data,CUDSS_DATA_MEMORY_ESTIMATES,estimates,sizeof(estimates),&written));
        if(written<6*sizeof(int64_t) || estimates[5]<0)
          throw std::runtime_error("invalid hybrid memory estimates");
        estimated_host_bytes=estimates[5];
      }
    }
    factor_s+=execute(CUDSS_PHASE_FACTORIZATION);
    int info=0; size_t written=0;
    DSS(cudssDataGet(handle,data,CUDSS_DATA_INFO,&info,sizeof(info),&written));
    if(info) throw std::runtime_error("factorization device error");
    solve_s+=execute(CUDSS_PHASE_SOLVE);
    for(int k=0;k<nrhs;++k) for(int i=0;i<n;++i) {
      if constexpr(native) result[k*n+i]=Complex(xv.p[k*dim+i].x,xv.p[k*dim+i].y);
      else result[k*n+i]=Complex(xv.p[k*dim+i],-xv.p[k*dim+i+n]);
    }
    // Independent host FP64 check in the original N-dimensional complex equation.
    for(int k=0;k<nrhs;++k) {
      double error=0,norm=0,residual=0,bnorm=0;
      for(int i=0;i<n;++i) {
        error+=std::norm(result[k*n+i]-exact[k*n+i]); norm+=std::norm(exact[k*n+i]);
        Complex action=0; for(auto [j,v]:source[i]) action+=v*result[k*n+j];
        residual+=std::norm(action-rhs[k*n+i]); bnorm+=std::norm(rhs[k*n+i]);
      }
      error_max=std::max(error_max,std::sqrt(error/norm));
      residual_max=std::max(residual_max,std::sqrt(residual/bnorm));
    }
  }
  DSS(cudssMatrixDestroy(a)); DSS(cudssMatrixDestroy(b)); DSS(cudssMatrixDestroy(x));
  DSS(cudssDataDestroy(handle,data)); DSS(cudssConfigDestroy(config)); DSS(cudssDestroy(handle));
  bool passed=std::isfinite(error_max) && std::isfinite(residual_max) && error_max<=1e-10 && residual_max<=1e-10 && allocation.live==0;
  std::printf("{\"mode\":\"%s\",\"n\":%d,\"dimension\":%d,\"nrhs\":2,\"updates\":2,\"relative_solution\":%.17g,\"relative_rhs_residual\":%.17g,\"cudss_peak_bytes\":%zu,\"cudss_live_after_destroy\":%zu,\"analysis_s\":%.9g,\"factor_s\":%.9g,\"solve_s\":%.9g,\"hybrid_limit_bytes\":%lld,\"minimum_device_bytes\":%lld,\"estimated_host_bytes\":%lld,\"passed\":%s}\n",
    native?"native_complex_fp64":"real_block_fp64",n,dim,error_max,residual_max,allocation.peak.load(),allocation.live.load(),analysis_s,factor_s,solve_s,(long long)limit_bytes,(long long)minimum_device_bytes,(long long)estimated_host_bytes,passed?"true":"false");
  std::fflush(stdout);
  if(!passed) throw std::runtime_error("quality/cleanup failed");
}

#ifndef PALACE_COARSE_PROBE_LIBRARY
int main() {
  try {
    int hybrid_mib=0;
    if(const char *value=std::getenv("PALACE_PROBE_HYBRID_MIB")) {
      char *end=nullptr; long parsed=std::strtol(value,&end,10);
      if(!value[0] || *end || parsed<256 || parsed>16384)
        throw std::runtime_error("invalid hybrid MiB budget");
      hybrid_mib=int(parsed);
    }
    run_case<cuDoubleComplex>(8,hybrid_mib); run_case<double>(8,hybrid_mib); return 0;
  }
  catch(const std::exception &error) { std::fprintf(stderr,"probe: %s\n",error.what()); return 1; }
}

#endif
