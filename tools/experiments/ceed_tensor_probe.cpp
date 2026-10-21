// SPDX-License-Identifier: Apache-2.0
// Isolated action probe; never replaces the Palace operator or its residual.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <vector>
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <ceed.h>
#include <ceed/backend.h>
#include <mfem.hpp>
#include <nlohmann/json.hpp>
#include "fem/libceed/basis.hpp"

using json=nlohmann::json;
extern "C" cudaError_t palace_probe_wmma(const float*,const double*,double*,int,int,int,int);
extern "C" cudaError_t palace_probe_pack(const double*,float*,size_t);
extern "C" cudaError_t palace_probe_unpack(const float*,double*,size_t,bool);
extern "C" cudaError_t palace_probe_fused_basis(const float*,const double*,double*,int,int,int,int,bool,bool);
extern "C" cudaError_t palace_probe_compensated(const float*,const float*,const double*,double*,int,int,int,int);
extern "C" cudaError_t palace_probe_compensated_bits(const float*,const float*,const double*,double*,int,int,int,int);
#define CUDA(x) do { auto code=(x);if(code!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(code)); } while(0)
#define CEED(x) do { if((x)!=0)throw std::runtime_error("libCEED failure: " #x); } while(0)
#define BLAS(x) do { auto code=(x);if(code!=CUBLAS_STATUS_SUCCESS)throw std::runtime_error("cuBLAS failure "+std::to_string(code)); } while(0)

#include "ceed_lt_probe.hpp"

template<class T> struct Buffer {
  T *raw=nullptr,*data=nullptr;size_t size;
  static constexpr size_t pad=8;
  explicit Buffer(size_t n):size(n) {
    CUDA(cudaMalloc(&raw,(n+2*pad)*sizeof(T)));data=raw+pad;
    T guards[pad];std::fill(guards,guards+pad,T(98765.125));
    CUDA(cudaMemcpy(raw,guards,sizeof(guards),cudaMemcpyHostToDevice));
    CUDA(cudaMemcpy(data+n,guards,sizeof(guards),cudaMemcpyHostToDevice));
  }
  ~Buffer(){if(raw)cudaFree(raw);}
  Buffer(const Buffer&)=delete;
  void write(const std::vector<T> &v){if(v.size()!=size)throw std::runtime_error("write length");CUDA(cudaMemcpy(data,v.data(),size*sizeof(T),cudaMemcpyHostToDevice));}
  std::vector<T> read(){std::vector<T> v(size);CUDA(cudaMemcpy(v.data(),data,size*sizeof(T),cudaMemcpyDeviceToHost));return v;}
  void check(){T g[2*pad];CUDA(cudaMemcpy(g,raw,pad*sizeof(T),cudaMemcpyDeviceToHost));CUDA(cudaMemcpy(g+pad,data+size,pad*sizeof(T),cudaMemcpyDeviceToHost));for(auto v:g)if(v!=T(98765.125))throw std::runtime_error("buffer canary corrupted");}
};

json error(const std::vector<double> &reference,const std::vector<double> &value,double tolerance) {
  if(reference.size()!=value.size())throw std::runtime_error("comparison length");
  long double diff=0,norm=0;double worst=0,peak=0;
  for(size_t i=0;i<value.size();++i){if(!std::isfinite(value[i])||!std::isfinite(reference[i]))throw std::runtime_error("nonfinite result");
    const double d=value[i]-reference[i];diff+=static_cast<long double>(d)*d;norm+=static_cast<long double>(reference[i])*reference[i];
    worst=std::max(worst,std::abs(d));peak=std::max(peak,std::abs(reference[i]));}
  // No absolute floors: tiny references must not hide relative errors.
  const double rel=norm>0?double(std::sqrt(diff/norm)):diff==0?0:std::numeric_limits<double>::max();
  const double scaled=peak>0?worst/peak:worst==0?0:std::numeric_limits<double>::max();
  return {{"relative_l2",rel},{"scaled_max",scaled},{"tolerance",tolerance},{"passed",rel<=tolerance&&scaled<=tolerance}};
}

// Independent long-double loop, component-major libCEED non-tensor layout.
std::vector<double> oracle(const std::vector<double>&b,const std::vector<double>&x,
                           const std::vector<double>&initial,int p,int q,int qc,int n,bool trans,bool add) {
  std::vector<double> y(initial.size());
  for(int e=0;e<n;++e) {
    if(!trans)for(int d=0;d<qc;++d)for(int j=0;j<q;++j){long double sum=0;
      for(int k=0;k<p;++k)sum+=static_cast<long double>(b[d*p*q+j*p+k])*x[e*p+k];
      y[size_t(d)*n*q+e*q+j]=double(sum);}
    else for(int k=0;k<p;++k){long double sum=add?initial[e*p+k]:0;
      for(int d=0;d<qc;++d)for(int j=0;j<q;++j)sum+=static_cast<long double>(b[d*p*q+j*p+k])*x[size_t(d)*n*q+e*q+j];
      y[e*p+k]=double(sum);}
  }
  return y;
}

template<class F> json timing(F apply) {
  apply();CUDA(cudaDeviceSynchronize()); // Exclude first-touch/JIT/library initialization.
  cudaEvent_t a,b;CUDA(cudaEventCreate(&a));CUDA(cudaEventCreate(&b));
  std::vector<double> gpu,wall;
  for(int i=0;i<3;++i){CUDA(cudaEventRecord(a));CUDA(cudaEventSynchronize(a));
    const auto start=std::chrono::steady_clock::now();apply();CUDA(cudaEventRecord(b));CUDA(cudaEventSynchronize(b));
    wall.push_back(std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count());
    float ms;CUDA(cudaEventElapsedTime(&ms,a,b));gpu.push_back(ms);}
  CUDA(cudaEventDestroy(a));CUDA(cudaEventDestroy(b));
  auto med=[](auto v){std::sort(v.begin(),v.end());return v[1];};
  return {{"wall_ms",wall},{"cuda_interval_ms",gpu},{"median_wall_ms",med(wall)},{"median_cuda_interval_ms",med(gpu)}};
}

template<class F> json linearity(F apply,Buffer<double>&dx,Buffer<double>&dy,const std::vector<double>&x,const std::vector<double>&bx,double tolerance) {
  const double alpha=1.23456789012345;std::vector<double> scaled(x),v(x.size()),sum(x.size());
  for(size_t i=0;i<x.size();++i){scaled[i]*=alpha;v[i]=.31*std::cos(.127*(i%1231));sum[i]=x[i]+v[i];}
  dx.write(scaled);apply();auto by=dy.read(),expected=bx;
  for(auto &value:expected)value*=alpha;
  auto homogeneous=error(expected,by,tolerance);
  dx.write(v);apply();by=dy.read();
  for(size_t i=0;i<by.size();++i)expected[i]=bx[i]+by[i];
  dx.write(sum);apply();auto superposition=error(expected,dy.read(),tolerance);
  dx.write(x);return {{"alpha",alpha},{"homogeneity",homogeneous},{"superposition",superposition},
    {"scope","Small independent columns of basis action only; not whole preconditioner defect or solver qualification"}};
}

template<class F> json range_stress(F apply,Buffer<double>&dx,Buffer<double>&dy,const std::vector<double>&x,
                                  const std::vector<double>&b,const std::vector<double>&initial,int p,int q,int qc,int n) {
  json result=json::array();
  for(double scale:{1e-300,1e-80,std::ldexp(1.,-75),std::ldexp(1.,-74),1e-30,1.,1e30,std::ldexp(1.,100),std::ldexp(1.,101),1e80,1e300}){
    auto input=x;for(auto &v:input)v*=scale;
    dx.write(input);apply();auto check=error(oracle(b,input,initial,p,q,qc,n,false,false),dy.read(),1e-11);
    result.push_back({{"scale",scale},{"accuracy",check}});
  }
  dx.write(x);return result;
}

json action(Ceed ceed,CeedBasis basis,cublasHandle_t handle,CeedEvalMode mode,int elements,int components,bool trans,bool add,bool fused,bool compensated,bool lt,bool wmma) {
  CeedInt p,q,qc;CEED(CeedBasisGetNumNodes(basis,&p));CEED(CeedBasisGetNumQuadraturePoints(basis,&q));CEED(CeedBasisGetNumQuadratureComponents(basis,mode,&qc));
  const double *tab=nullptr;
  if(mode==CEED_EVAL_INTERP)CEED(CeedBasisGetInterp(basis,&tab));
  else if(mode==CEED_EVAL_CURL)CEED(CeedBasisGetCurl(basis,&tab));
  else if(mode==CEED_EVAL_DIV)CEED(CeedBasisGetDiv(basis,&tab));
  else CEED(CeedBasisGetGrad(basis,&tab));
  const int n=elements*components;const size_t ni=size_t(n)*(trans?q*qc:p),no=size_t(n)*(trans?p:q*qc);
  std::vector<double> coefficients(tab,tab+p*q*qc),input(ni),initial(no);
  for(size_t i=0;i<ni;++i)input[i]=std::sin(.173*(i%1009))+.125*std::cos(.071*(i%1013));
  for(size_t i=0;i<no;++i)initial[i]=.2*std::sin(.11*(i%997));
  Buffer<double> db(coefficients.size()),dx(ni),dy(no);Buffer<float> fb(coefficients.size()),fx(ni),fy(no);
  db.write(coefficients);dx.write(input);dy.write(initial);
  const auto setup_start=std::chrono::steady_clock::now();
  CUDA(palace_probe_pack(db.data,fb.data,db.size));CUDA(cudaDeviceSynchronize());
  const double basis_pack_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-setup_start).count();
  std::unique_ptr<Buffer<float>> lower;
  double low_pack_ms=0;
  if(compensated&&!trans){const auto t=std::chrono::steady_clock::now();
    std::vector<float> residual(coefficients.size());
    for(size_t i=0;i<residual.size();++i)residual[i]=float(coefficients[i]-double(float(coefficients[i])));
    lower=std::make_unique<Buffer<float>>(residual.size());lower->write(residual);
    low_pack_ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-t).count();}
  if(fused&&palace_probe_fused_basis(fb.data,dx.data,dy.data,7,q,qc,n,trans,add)!=cudaErrorNotSupported)
    throw std::runtime_error("fused unsupported-shape guard failed");
  CeedVector u,v;CEED(CeedVectorCreate(ceed,ni,&u));CEED(CeedVectorCreate(ceed,no,&v));
  CEED(CeedVectorSetArray(u,CEED_MEM_DEVICE,CEED_USE_POINTER,dx.data));CEED(CeedVectorSetArray(v,CEED_MEM_DEVICE,CEED_USE_POINTER,dy.data));
  auto native=[&] {if(add)CEED(CeedBasisApplyAdd(basis,elements,CEED_TRANSPOSE,mode,u,v));else CEED(CeedBasisApply(basis,elements,trans?CEED_TRANSPOSE:CEED_NOTRANSPOSE,mode,u,v));};
  native();auto ref=dy.read();
  json result={{"P",p},{"Q",q},{"q_components",qc},{"components",components},{"elements",elements},{"N",n},{"eval",int(mode)},{"transpose",trans},{"add",add},
    {"input_bytes",ni*8},{"output_bytes",no*8},{"extra_fp32_workspace_bytes",(ni+no+db.size)*4},{"basis_pack_once_ms",basis_pack_ms},{"low_basis_pack_once_ms",low_pack_ms}};
  if(elements==257){auto cpu=oracle(coefficients,input,initial,p,q,qc,n,trans,add);result["original_vs_cpu"]=error(cpu,ref,1e-11);
    if(!result["original_vs_cpu"]["passed"].get<bool>())throw std::runtime_error("original libCEED vs independent CPU oracle failed");
    auto bad=ref;bad[0]+=1+2*std::abs(*std::max_element(ref.begin(),ref.end(),[](double a,double b){return std::abs(a)<std::abs(b);}));
    if(error(ref,bad,2e-3)["passed"].get<bool>())throw std::runtime_error("fault detector failed");}
  // Timings intentionally don't reset ApplyAdd between repeats: every method
  // accumulates another result, without any reset/copy hidden inside its timing.
  if(compensated&&!trans&&elements==257){result["original_linearity"]=linearity(native,dx,dy,input,ref,1e-11);
    if(!result["original_linearity"]["homogeneity"]["passed"].get<bool>()||!result["original_linearity"]["superposition"]["passed"].get<bool>())throw std::runtime_error("original linearity control failed");}
  dy.write(initial);result["original_timing"]=timing(native);
  json methods=json::array();
  for(int precision=0;precision<(compensated&&!trans?6:fused?4:3);++precision){const bool mixed=precision!=0;const double tol=(precision==0||precision>=4)?1e-11:(precision==2?2e-3:2e-6);
    auto apply=[&]{if(precision==5){CUDA(palace_probe_compensated_bits(fb.data,lower->data,dx.data,dy.data,p,q,qc,n));return;}
      if(precision==4){CUDA(palace_probe_compensated(fb.data,lower->data,dx.data,dy.data,p,q,qc,n));return;}
      if(precision==3){CUDA(palace_probe_fused_basis(fb.data,dx.data,dy.data,p,q,qc,n,trans,add));return;}
      if(mixed)CUDA(palace_probe_pack(dx.data,fx.data,ni));
      for(int d=0;d<qc;++d){const double alpha=1,beta=trans?(d>0||(!mixed&&add)?1:0):0;const float af=1,bf=float(trans&&d>0);
        const int m=trans?p:q,k=trans?q:p;const auto op=trans?CUBLAS_OP_N:CUBLAS_OP_T;
        const size_t xo=trans?size_t(d)*n*q:0,yo=trans?0:size_t(d)*n*q;
        if(!mixed)BLAS(cublasDgemm(handle,op,CUBLAS_OP_N,m,n,k,&alpha,db.data+d*p*q,p,dx.data+xo,k,&beta,dy.data+yo,m));
        else BLAS(cublasGemmEx(handle,op,CUBLAS_OP_N,m,n,k,&af,fb.data+d*p*q,CUDA_R_32F,p,fx.data+xo,CUDA_R_32F,k,&bf,fy.data+yo,CUDA_R_32F,m,
          precision==1?CUBLAS_COMPUTE_32F_PEDANTIC:CUBLAS_COMPUTE_32F_FAST_TF32,CUBLAS_GEMM_DEFAULT));}
      if(mixed)CUDA(palace_probe_unpack(fy.data,dy.data,no,add));};
    dy.write(initial);apply();auto value=dy.read();json check=error(ref,value,tol);
    if(elements==257)check["independent_cpu"]=error(oracle(coefficients,input,initial,p,q,qc,n,trans,add),value,tol);
    json test;
    if(compensated&&!trans&&elements==257)test=linearity(apply,dx,dy,input,value,tol);
    json stress;if(precision==5&&elements==257)stress=range_stress(apply,dx,dy,input,coefficients,initial,p,q,qc,n);
    dy.write(initial);methods.push_back({{"precision",precision==0?"FP64":precision==1?"FP32_pedantic":precision==2?"TF32_requested":precision==3?"FP32_fused":precision==4?"mixed_compensated":"mixed_compensated_bits"},{"accuracy",check},{"timing",timing(apply)},
      {"linearity",test},{"range_stress",stress},{"extra_fp32_workspace_bytes",precision>=4?db.size*8:precision==3?db.size*4:precision==0?0:(ni+no+db.size)*4}});
  }
  if(lt){
    const auto start=std::chrono::steady_clock::now();
    std::vector<std::unique_ptr<LtBasisPlan>> plans;json components_meta=json::array();bool supported=true;
    for(int d=0;d<qc;++d){
      const size_t xo=trans?size_t(d)*n*q:0,yo=trans?0:size_t(d)*n*q;
      plans.push_back(std::make_unique<LtBasisPlan>(p,q,n,trans,fb.data+d*p*q,fx.data+xo,fy.data+yo));
      supported=supported&&plans.back()->supported;components_meta.push_back(plans.back()->metadata);
    }
    json test={{"precision","TF32_Lt"},{"supported",supported},{"plans",components_meta},
      {"plan_ms",std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()},
      {"extra_fp32_workspace_bytes",(ni+no+db.size)*4},{"workspace_limit_bytes",LtBasisPlan::workspace_limit}};
    if(supported){
      void *workspace=nullptr;CUDA(cudaMalloc(&workspace,LtBasisPlan::workspace_limit));
      std::shared_ptr<void> guard(workspace,[](void *v){cudaFree(v);});
      auto apply=[&]{CUDA(palace_probe_pack(dx.data,fx.data,ni));
        for(int d=0;d<qc;++d){const size_t xo=trans?size_t(d)*n*q:0,yo=trans?0:size_t(d)*n*q;
          plans[d]->apply(fb.data+d*p*q,fx.data+xo,fy.data+yo,float(trans&&d>0),workspace);}
        CUDA(palace_probe_unpack(fy.data,dy.data,no,add));};
      dy.write(initial);apply();auto value=dy.read();test["accuracy"]=error(ref,value,2e-3);
      if(elements==257)test["accuracy"]["independent_cpu"]=error(oracle(coefficients,input,initial,p,q,qc,n,trans,add),value,2e-3);
      dy.write(initial);test["timing"]=timing(apply);
    }
    methods.push_back(test);
  }
  if(wmma&&!trans){
    if(palace_probe_wmma(fb.data,dx.data,dy.data,19,q,qc,n)!=cudaErrorNotSupported)
      throw std::runtime_error("WMMA unsupported shape guard failed");
    auto apply=[&]{CUDA(palace_probe_wmma(fb.data,dx.data,dy.data,p,q,qc,n));};
    dy.write(initial);apply();auto value=dy.read();auto check=error(ref,value,2e-3);
    if(elements==257)check["independent_cpu"]=error(oracle(coefficients,input,initial,p,q,qc,n,false,false),value,2e-3);
    methods.push_back({{"precision","TF32_WMMA_fused"},{"accuracy",check},{"timing",timing(apply)},
      {"extra_fp32_workspace_bytes",db.size*4},{"shared_bytes_per_block",(3*16*32+32*64+16*64)*4}});
  }
  result["methods"]=methods;db.check();dx.check();dy.check();fb.check();fx.check();fy.check();result["canaries_passed"]=true;
  if(lower)lower->check();
  CEED(CeedVectorDestroy(&u));CEED(CeedVectorDestroy(&v));return result;
}

int main(int argc,char**argv){
  try{
    if(argc<2||argc>7)throw std::runtime_error("expected output path [scale] [fused] [compensated] [lt] [wmma]");
    bool scale=false,fused=false,compensated=false,lt=false,wmma=false;
    for(int i=2;i<argc;++i){if(std::string(argv[i])=="scale"&&!scale)scale=true;
      else if(std::string(argv[i])=="fused"&&!fused)fused=true;
      else if(std::string(argv[i])=="wmma"&&!wmma)wmma=true;
      else if(std::string(argv[i])=="lt"&&!lt)lt=true;
      else if(std::string(argv[i])=="compensated"&&!compensated)compensated=true;else throw std::runtime_error("invalid/duplicate suite option");}
    if(compensated&&!fused)throw std::runtime_error("compensated requires fused comparator");
    if(wmma&&(!lt||!fused))throw std::runtime_error("WMMA requires Lt and fused comparators");
    if(compensated&&lt)throw std::runtime_error("Lt and compensated are separate experiments");
    if(error({0},{1e-300},1e-11)["passed"].get<bool>()||error({1e-300},{1.001e-300},1e-11)["passed"].get<bool>())
      throw std::runtime_error("tiny-relative-error fault detector failed");
    if(palace_probe_fused_basis(nullptr,nullptr,nullptr,20,14,3,0,false,false)!=cudaErrorInvalidValue)
      throw std::runtime_error("fused argument guard failed");
    mfem::Mpi::Init(argc,argv);mfem::Device device("cpu");
    Ceed ceed;CEED(CeedInit("/gpu/cuda/magma",&ceed));cublasHandle_t handle;BLAS(cublasCreate(&handle));
    cudaDeviceProp prop;CUDA(cudaGetDeviceProperties(&prop,0));int blas_version;BLAS(cublasGetVersion(handle,&blas_version));
    json report={{"scope","Isolated GPU-resident basis actions; not UVM, solver speedup or RF qualification. TF32 request is not proof of Tensor Core instructions."},
      {"gpu",prop.name},{"cublas_version",blas_version},{"suite",scale?"scale":"screen"},{"fused",fused},{"compensated",compensated},
      {"lt",lt},{"wmma",wmma},{"compensated_bits",compensated},{"tiny_error_controls",true},{"rows",json::array()}};
    // MFEM caches tabulations by rule address: retain mapped rules until FE teardown.
    std::vector<std::unique_ptr<mfem::IntegrationRule>> mapped_rules;
    mfem::ND_FECollection nd(2,3),nd2(2,2);mfem::RT_FECollection rt(1,3);mfem::H1_FECollection h1(2,3);
    for(int family=0;family<4;++family)for(int points:{6,14}) {
      if((scale||lt)&&(family!=0||points!=14))continue;
      if(family==3&&points==14)continue;
      const auto geom=family==3?mfem::Geometry::TRIANGLE:mfem::Geometry::TETRAHEDRON;
      const auto *fe=(family==0?nd.FiniteElementForGeometry(geom):family==1?rt.FiniteElementForGeometry(geom):family==2?h1.FiniteElementForGeometry(geom):nd2.FiniteElementForGeometry(geom));
      if(fe->GetDof()!=(family==0?20:family==1?15:family==2?10:8))throw std::runtime_error("unexpected actual basis P");
      // Q6 on a tet is a representative mapped face trace, not a six-point
      // tetrahedron volume rule. Metadata alone doesn't identify exact trace points.
      const bool trace=family!=3&&points==6;
      const auto rule_geom=trace?mfem::Geometry::TRIANGLE:geom;
      int degree=0;for(;degree<=8;++degree)if(mfem::IntRules.Get(rule_geom,degree).GetNPoints()==points)break;
      if(degree>8)throw std::runtime_error("quadrature unavailable");
      const auto *ir=&mfem::IntRules.Get(rule_geom,degree);CeedBasis basis;
      if(trace){auto mapped=std::make_unique<mfem::IntegrationRule>(points);
        for(int i=0;i<points;++i){mapped->IntPoint(i)=ir->IntPoint(i);mapped->IntPoint(i).z=0;}
        ir=mapped.get();mapped_rules.push_back(std::move(mapped));}
      for(int components:{1,2}){
      if((scale||lt)&&components!=1)continue;
      if(components==2&&!(family==0&&points==14))continue;
      palace::ceed::InitBasisFromRule(*fe,*ir,components,ceed,&basis);
      for(auto mode:{CEED_EVAL_INTERP,(family==0||family==3)?CEED_EVAL_CURL:family==1?CEED_EVAL_DIV:CEED_EVAL_GRAD})
        for(int elems:(scale?std::vector<int>{257,1023,4099,16383,65537,131071,1601320}:std::vector<int>{257,131071}))for(int variant=0;variant<3;++variant) {
          auto row=action(ceed,basis,handle,mode,elems,components,variant!=0,variant==2,fused,compensated,lt,wmma);row["family"]=family;row["rule_degree"]=degree;
          row["rule_source"]=trace?"representative_triangle_z0_trace":family==3?"triangle":"tet_volume";
          report["rows"].push_back(row);std::cout<<"completed family="<<family<<" Q="<<points<<" mode="<<int(mode)<<" n="<<elems<<" variant="<<variant<<std::endl;
        }
      CEED(CeedBasisDestroy(&basis));
      }
    }
    BLAS(cublasDestroy(handle));CEED(CeedDestroy(&ceed));report["complete"]=true;
    std::ofstream out(argv[1]);out<<report.dump(2)<<'\n';if(!out)throw std::runtime_error("output failed");
    return 0;
  }catch(const std::exception &e){std::cerr<<e.what()<<std::endl;return 1;}
}
