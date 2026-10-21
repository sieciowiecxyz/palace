// SPDX-License-Identifier: Apache-2.0
// Experimental complex FP32 factors with independent original-FP64 refinement checks.
#define PALACE_COARSE_PROBE_LIBRARY
#include "complex_coarse_probe.cu"
#include <limits>
#include "../../palace/linalg/mixedcoarse.hpp"
namespace mc=palace::mixedcoarse;

struct Error {
  double solution=0, residual=0, backward=0;
};

using Rows=std::vector<std::map<int,Complex>>;

std::vector<Complex> action(const Rows &a, const std::vector<Complex> &x, int nrhs) {
  const int n=int(a.size());
  std::vector<Complex> y(n*nrhs);
  for(int k=0;k<nrhs;++k) for(int i=0;i<n;++i)
    for(auto [j,v]:a[i]) y[k*n+i]+=v*x[k*n+j];
  for(auto value:y)if(!std::isfinite(value.real())||!std::isfinite(value.imag()))
    throw std::runtime_error("nonfinite original FP64 action");
  return y;
}

Error error(const Rows &a,const std::vector<Complex> &x,const std::vector<Complex> &exact,
            const std::vector<Complex> &b,int nrhs) {
  for(auto value:x)if(!std::isfinite(value.real())||!std::isfinite(value.imag()))
    throw std::runtime_error("nonfinite computed solution");
  auto ax=action(a,x,nrhs); const int n=int(a.size()); Error out;
  for(int k=0;k<nrhs;++k) {
    double diff=0,norm=0,res=0,bnorm=0;
    for(int i=0;i<n;++i) {
      auto r=b[k*n+i]-ax[k*n+i];
      diff+=std::norm(x[k*n+i]-exact[k*n+i]); norm+=std::norm(exact[k*n+i]);
      res+=std::norm(r); bnorm+=std::norm(b[k*n+i]);
      double denominator=std::abs(b[k*n+i]);
      for(auto [j,v]:a[i]) denominator+=std::abs(v)*std::abs(x[k*n+j]);
      if(denominator>0) out.backward=std::max(out.backward,std::abs(r)/denominator);
      else if(std::abs(r)>0) out.backward=std::numeric_limits<double>::infinity();
    }
    out.solution=std::max(out.solution,std::sqrt(diff/norm));
    out.residual=std::max(out.residual,std::sqrt(res/bnorm));
  }
  return out;
}

template<class T> T pack(Complex z);
template<> cuDoubleComplex pack(Complex z) {return make_cuDoubleComplex(z.real(),z.imag());}
template<> cuComplex pack(Complex z) {
  float r=float(z.real()),i=float(z.imag());
  if(!std::isfinite(r)||!std::isfinite(i)) throw std::runtime_error("FP32 overflow");
  return make_cuComplex(r,i);
}
template<class T> Complex unpack(T z) {return Complex(z.x,z.y);}

// Independent CPU checks, odd launch sizes and end canaries for every GPU helper.
void helper_checks() {
  auto require=[](bool ok) {if(!ok)throw std::runtime_error("mixed CUDA helper boundary/value check");};
  require(mc::Pack(-1,2,nullptr,nullptr,nullptr)==cudaErrorInvalidValue);
  require(mc::Accumulate(1,0,nullptr,nullptr,nullptr,false)==cudaErrorInvalidValue);
  require(mc::Residual(INT_MAX,2,nullptr,nullptr,nullptr,nullptr,nullptr,nullptr)==cudaErrorInvalidValue);
  require(mc::MatrixPack(-1,nullptr,nullptr,nullptr,nullptr,nullptr)==cudaErrorInvalidValue);
  require(mc::Scale(0,4)==.5 && mc::Scale(4,8)==.5 && mc::Scale(0,0)==0
    && mc::Scale(std::numeric_limits<double>::quiet_NaN(),1)==0);
  {
    Buffer<int> invalid(1);Buffer<double> d(1);Buffer<cuDoubleComplex> x(1);Buffer<cuComplex> y(1);
    invalid.p[0]=0;d.p[0]=1;x.p[0]=make_cuDoubleComplex(1e300,0);
    CUDA(mc::Pack(1,1,d.p,x.p,y.p,nullptr,invalid.p));CUDA(cudaDeviceSynchronize());
    require(invalid.p[0]==1);
    invalid.p[0]=0;x.p[0]=make_cuDoubleComplex(1,0);
    CUDA(mc::Pack(1,1,d.p,x.p,y.p,nullptr,invalid.p));CUDA(cudaDeviceSynchronize());
    require(invalid.p[0]==0);
  }
  for(int n:{0,1,509,1009}) {
    const int count=2*n;
    Rows a(n);std::vector<int> offsets(n+1),columns;
    for(int i=0;i<n;++i) {
      offsets[i]=int(columns.size());a[i][i]=Complex(2+.001*i,.5);
      if(i+1<n)a[i][i+1]=Complex(-.3,.2);
      if(i)a[i][i-1]=Complex(.1,-.4);
      for(auto [j,v]:a[i])columns.push_back(j);
    }
    const int nnz=int(columns.size());offsets[n]=nnz;
    Buffer<int> ri(n+1),ci(nnz+1);
    Buffer<double> d(n+1);
    Buffer<cuDoubleComplex> av(nnz+1),x(count+1),b(count+1),y(count+1),r(count+1);
    Buffer<cuComplex> packed(count+1),matrix32(nnz+1);
    std::copy(offsets.begin(),offsets.end(),ri.p);std::copy(columns.begin(),columns.end(),ci.p);
    int pos=0;for(int i=0;i<n;++i)for(auto [j,v]:a[i])av.p[pos++]=pack<cuDoubleComplex>(v);
    std::vector<Complex> hx(count),hb(count);
    for(int i=0;i<n;++i)d.p[i]=.5+.0003*i;
    for(int i=0;i<count;++i) {
      hx[i]=Complex(std::sin(.1*i),std::cos(.3*i));hb[i]=Complex(.05*i,-.03*i);
      x.p[i]=pack<cuDoubleComplex>(hx[i]);b.p[i]=pack<cuDoubleComplex>(hb[i]);
    }
    const Complex sentinel(123,-456);
    packed.p[count]=pack<cuComplex>(sentinel);matrix32.p[nnz]=pack<cuComplex>(sentinel);
    y.p[count]=pack<cuDoubleComplex>(sentinel);r.p[count]=pack<cuDoubleComplex>(sentinel);
    CUDA(mc::Pack(n,2,d.p,x.p,packed.p));CUDA(mc::MatrixPack(n,ri.p,ci.p,av.p,d.p,matrix32.p));
    CUDA(mc::Accumulate(n,2,d.p,packed.p,y.p,false));
    CUDA(mc::Residual(n,2,ri.p,ci.p,av.p,x.p,b.p,r.p));CUDA(cudaDeviceSynchronize());
    auto ax=action(a,hx,2);
    for(int i=0;i<count;++i) {
      const auto rounded=unpack(pack<cuComplex>(d.p[i%n]*hx[i]));
      require(unpack(packed.p[i])==rounded);
      require(std::abs(unpack(y.p[i])-d.p[i%n]*rounded)<1e-14);
      require(std::abs(unpack(r.p[i])-(hb[i]-ax[i]))<1e-13);
    }
    pos=0;for(int i=0;i<n;++i)for(auto [j,v]:a[i]) {
      require(unpack(matrix32.p[pos++])==unpack(pack<cuComplex>((d.p[i]*d.p[j])*v)));
    }
    CUDA(mc::Accumulate(n,2,d.p,packed.p,y.p,true));CUDA(cudaDeviceSynchronize());
    for(int i=0;i<count;++i)require(std::abs(unpack(y.p[i])-2*d.p[i%n]*unpack(packed.p[i]))<1e-14);
    require(unpack(packed.p[count])==sentinel && unpack(matrix32.p[nnz])==sentinel
      && unpack(y.p[count])==sentinel && unpack(r.p[count])==sentinel);
  }
  std::puts("PALACE_MIXED_COARSE_HELPERS: cases=4 passed=1");
  std::fflush(stdout);
}

template<class T> void mixed_case(bool ill_scaled,bool equilibrate,int corrections) {
  constexpr bool fp32=std::is_same<T,cuComplex>::value;
  constexpr int side=8,n=side*side*side,nrhs=2,updates=2;
  const auto dtype=fp32?CUDA_C_32F:CUDA_C_64F;
  auto a=matrix(side,0);
  std::vector<int> offsets(n+1),columns;
  for(int i=0;i<n;++i) {offsets[i]=int(columns.size());for(auto [j,v]:a[i])columns.push_back(j);}
  offsets[n]=int(columns.size());
  Buffer<int> ri(offsets.size()),ci(columns.size());
  Buffer<T> av(columns.size()),bv(n*nrhs),xv(n*nrhs);
  Buffer<double> dscale(n);
  Buffer<cuDoubleComplex> original(columns.size()),original_rhs(n*nrhs),gpu_x(n*nrhs),gpu_r(n*nrhs);
  std::copy(offsets.begin(),offsets.end(),ri.p); std::copy(columns.begin(),columns.end(),ci.p);
  Allocation allocation;
  cudssHandle_t handle; cudssConfig_t config; cudssData_t data; cudssMatrix_t am,bm,xm;
  DSS(cudssCreate(&handle)); cudssDeviceMemHandler_t handler{};
  handler.ctx=&allocation; handler.device_alloc=Allocation::alloc;handler.device_free=Allocation::free;
  std::snprintf(handler.name,sizeof(handler.name),"mixed probe RAM/VRAM");
  DSS(cudssSetDeviceMemHandler(handle,&handler));
  DSS(cudssConfigCreate(&config));DSS(cudssDataCreate(handle,&data));
  // Disable library IR: all corrections below use the ORIGINAL FP64 operator.
  int zero=0;DSS(cudssConfigSet(config,CUDSS_CONFIG_IR_N_STEPS,&zero,sizeof(zero)));
  DSS(cudssMatrixCreateCsr(&am,n,n,columns.size(),ri.p,nullptr,ci.p,av.p,CUDA_R_32I,dtype,
                         CUDSS_MTYPE_GENERAL,CUDSS_MVIEW_FULL,CUDSS_BASE_ZERO));
  DSS(cudssMatrixCreateDn(&bm,n,nrhs,n,bv.p,dtype,CUDSS_LAYOUT_COL_MAJOR));
  DSS(cudssMatrixCreateDn(&xm,n,nrhs,n,xv.p,dtype,CUDSS_LAYOUT_COL_MAJOR));
  double analysis_s=0,factor_s=0,solve_s=0,check_s=0; Error worst;
  bool fault_rejected=true; double min_scale=std::numeric_limits<double>::infinity(),max_scale=0;
  auto execute=[&](int phase) {
    CUDA(cudaDeviceSynchronize()); auto t=Clock::now();
    DSS(cudssExecute(handle,phase,config,data,am,xm,bm));CUDA(cudaDeviceSynchronize());
    return std::chrono::duration<double>(Clock::now()-t).count();
  };
  for(int update=0;update<updates;++update) {
    a=matrix(side,update);std::vector<double> gamma(n,1),scale(n,1);
    if(ill_scaled) for(int i=0;i<n;++i)gamma[i]=std::pow(10.0,-3.0+6.0*i/(n-1));
    for(int i=0;i<n;++i)for(auto &[j,v]:a[i])v*=gamma[i]*gamma[j];
    if(equilibrate)for(int i=0;i<n;++i) {
      const double diag=std::abs(a[i].at(i));
      if(!std::isfinite(diag)||diag<=0)throw std::runtime_error("invalid diagonal scaling");
      scale[i]=1/std::sqrt(diag);
    }
    min_scale=std::min(min_scale,*std::min_element(scale.begin(),scale.end()));
    max_scale=std::max(max_scale,*std::max_element(scale.begin(),scale.end()));
    std::copy(scale.begin(),scale.end(),dscale.p);
    int pos=0;for(int i=0;i<n;++i)for(auto [j,v]:a[i]) {
      original.p[pos]=pack<cuDoubleComplex>(v);
      if constexpr(!fp32)av.p[pos]=pack<T>(v);
      ++pos;
    }
    if constexpr(fp32) CUDA(mc::MatrixPack(n,ri.p,ci.p,original.p,dscale.p,av.p));
    std::vector<Complex> exact(n*nrhs);
    for(int k=0;k<nrhs;++k)for(int i=0;i<n;++i)
      exact[k*n+i]=Complex(std::sin((i+1)*.13+k),std::cos((i+1)*.07-k));
    const auto b=action(a,exact,nrhs);
    for(int i=0;i<n*nrhs;++i)original_rhs.p[i]=pack<cuDoubleComplex>(b[i]);
    DSS(cudssMatrixSetValues(am,av.p));
    if(!update)analysis_s=execute(CUDSS_PHASE_ANALYSIS);
    factor_s+=execute(CUDSS_PHASE_FACTORIZATION);
    int info=0;size_t written=0;DSS(cudssDataGet(handle,data,CUDSS_DATA_INFO,&info,sizeof(info),&written));
    if(info||written!=sizeof(info))throw std::runtime_error("mixed factorization error");
    std::vector<Complex> x(n*nrhs),residual=b;
    // Initial solve plus exactly the prescribed number of correction solves.
    for(int step=0;step<=corrections;++step) {
      auto t=Clock::now();
      if constexpr(fp32) {
        if(step) CUDA(mc::Residual(n,nrhs,ri.p,ci.p,original.p,gpu_x.p,original_rhs.p,gpu_r.p));
        CUDA(mc::Pack(n,nrhs,dscale.p,step?gpu_r.p:original_rhs.p,bv.p));
        CUDA(cudaDeviceSynchronize());
      }else{
        for(int k=0;k<nrhs;++k)for(int i=0;i<n;++i)bv.p[k*n+i]=pack<T>(residual[k*n+i]*scale[i]);
      }
      check_s+=std::chrono::duration<double>(Clock::now()-t).count();
      DSS(cudssMatrixSetValues(bm,bv.p));DSS(cudssMatrixSetValues(xm,xv.p));
      solve_s+=execute(CUDSS_PHASE_SOLVE);
      t=Clock::now();
      if constexpr(fp32) {
        CUDA(mc::Accumulate(n,nrhs,dscale.p,xv.p,gpu_x.p,step!=0));
        CUDA(cudaDeviceSynchronize());
      }else{
        for(int k=0;k<nrhs;++k)for(int i=0;i<n;++i)x[k*n+i]+=unpack(xv.p[k*n+i])*scale[i];
        auto ax=action(a,x,nrhs);
        for(int i=0;i<n*nrhs;++i)residual[i]=b[i]-ax[i];
      }
      check_s+=std::chrono::duration<double>(Clock::now()-t).count();
    }
    if constexpr(fp32) for(int i=0;i<n*nrhs;++i)x[i]=unpack(gpu_x.p[i]);
    auto e=error(a,x,exact,b,nrhs);worst.solution=std::max(worst.solution,e.solution);
    worst.residual=std::max(worst.residual,e.residual);worst.backward=std::max(worst.backward,e.backward);
    auto corrupt=x;corrupt[0]+=Complex(.1,.05);auto bad=error(a,corrupt,exact,b,nrhs);
    fault_rejected=fault_rejected && bad.solution>1e-6 && bad.backward>1e-6;
  }
  DSS(cudssDataDestroy(handle,data));DSS(cudssMatrixDestroy(am));DSS(cudssMatrixDestroy(bm));
  DSS(cudssMatrixDestroy(xm));DSS(cudssConfigDestroy(config));DSS(cudssDestroy(handle));
  const double threshold=fp32&&!equilibrate?1e-2:1e-10;
  bool passed=std::isfinite(worst.solution)&&std::isfinite(worst.residual)&&std::isfinite(worst.backward)
    &&worst.solution<=threshold&&worst.residual<=threshold&&worst.backward<=threshold
    &&fault_rejected&&allocation.live==0;
  const char *mode=!fp32?"fp64":equilibrate?"scaled_refined_fp32":"raw_fp32";
  std::printf("{\"case\":\"%s\",\"mode\":\"%s\",\"n\":512,\"nrhs\":2,\"updates\":2,\"corrections\":%d,\"factor_dtype\":\"%s\",\"residual_dtype\":\"complex_fp64\",\"relative_solution\":%.17g,\"relative_rhs_residual\":%.17g,\"componentwise_backward_error\":%.17g,\"scale_min\":%.17g,\"scale_max\":%.17g,\"fault_rejected\":%s,\"cudss_peak_bytes\":%zu,\"cudss_live_after_destroy\":%zu,\"analysis_s\":%.9g,\"factor_s\":%.9g,\"solve_s\":%.9g,\"correction_s\":%.9g,\"correction_backend\":\"%s\",\"passed\":%s}\n",
    ill_scaled?"ill_scaled":"regular",mode,corrections,fp32?"complex_fp32":"complex_fp64",
    worst.solution,worst.residual,worst.backward,min_scale,max_scale,fault_rejected?"true":"false",
    allocation.peak.load(),allocation.live.load(),analysis_s,factor_s,solve_s,check_s,fp32?"cuda_fp64":"host_fp64",passed?"true":"false");
  std::fflush(stdout);
  // Ill-scaled raw FP32 is a diagnostic negative control, not a candidate gate.
  // Preserve passed=false and continue to the REQUIRED scaled/refined case.
  if(!passed && !(ill_scaled && fp32 && !equilibrate && fault_rejected && allocation.live==0))
    throw std::runtime_error("mixed case quality/cleanup failed");
}

int main() {
  try {
    helper_checks();
    for(bool ill:{false,true}) {
      mixed_case<cuDoubleComplex>(ill,false,0);
      mixed_case<cuComplex>(ill,false,0);
      mixed_case<cuComplex>(ill,true,2);
    }
    return 0;
  }catch(const std::exception &e){std::fprintf(stderr,"mixed probe: %s\n",e.what());return 1;}
}
