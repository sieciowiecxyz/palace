// SPDX-License-Identifier: Apache-2.0
// Isolated action probe; never replaces the Palace operator or its residual.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
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
extern "C" cudaError_t palace_probe_pack(const double*,float*,size_t);
extern "C" cudaError_t palace_probe_unpack(const float*,double*,size_t,bool);
extern "C" cudaError_t palace_probe_fused_basis(const float*,const double*,double*,int,int,int,int,bool,bool);
#define CUDA(x) do { auto code=(x);if(code!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(code)); } while(0)
#define CEED(x) do { if((x)!=0)throw std::runtime_error("libCEED failure: " #x); } while(0)
#define BLAS(x) do { auto code=(x);if(code!=CUBLAS_STATUS_SUCCESS)throw std::runtime_error("cuBLAS failure "+std::to_string(code)); } while(0)

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
  const double rel=std::sqrt(double(diff/std::max(norm,1e-300L))),scaled=worst/std::max(peak,1e-150);
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

json action(Ceed ceed,CeedBasis basis,cublasHandle_t handle,CeedEvalMode mode,int elements,int components,bool trans,bool add,bool fused) {
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
  if(fused&&palace_probe_fused_basis(fb.data,dx.data,dy.data,7,q,qc,n,trans,add)!=cudaErrorNotSupported)
    throw std::runtime_error("fused unsupported-shape guard failed");
  CeedVector u,v;CEED(CeedVectorCreate(ceed,ni,&u));CEED(CeedVectorCreate(ceed,no,&v));
  CEED(CeedVectorSetArray(u,CEED_MEM_DEVICE,CEED_USE_POINTER,dx.data));CEED(CeedVectorSetArray(v,CEED_MEM_DEVICE,CEED_USE_POINTER,dy.data));
  auto native=[&] {if(add)CEED(CeedBasisApplyAdd(basis,elements,CEED_TRANSPOSE,mode,u,v));else CEED(CeedBasisApply(basis,elements,trans?CEED_TRANSPOSE:CEED_NOTRANSPOSE,mode,u,v));};
  native();auto ref=dy.read();
  json result={{"P",p},{"Q",q},{"q_components",qc},{"components",components},{"elements",elements},{"N",n},{"eval",int(mode)},{"transpose",trans},{"add",add},
    {"input_bytes",ni*8},{"output_bytes",no*8},{"extra_fp32_workspace_bytes",(ni+no+db.size)*4},{"basis_pack_once_ms",basis_pack_ms}};
  if(elements==257){auto cpu=oracle(coefficients,input,initial,p,q,qc,n,trans,add);result["original_vs_cpu"]=error(cpu,ref,1e-11);
    if(!result["original_vs_cpu"]["passed"].get<bool>())throw std::runtime_error("original libCEED vs independent CPU oracle failed");
    auto bad=ref;bad[0]+=1+2*std::abs(*std::max_element(ref.begin(),ref.end(),[](double a,double b){return std::abs(a)<std::abs(b);}));
    if(error(ref,bad,2e-3)["passed"].get<bool>())throw std::runtime_error("fault detector failed");}
  // Timings intentionally don't reset ApplyAdd between repeats: every method
  // accumulates another result, without any reset/copy hidden inside its timing.
  dy.write(initial);result["original_timing"]=timing(native);
  json methods=json::array();
  for(int precision=0;precision<(fused?4:3);++precision){const bool mixed=precision!=0;const double tol=precision==0?1e-11:(precision==2?2e-3:2e-6);
    auto apply=[&]{if(precision==3){CUDA(palace_probe_fused_basis(fb.data,dx.data,dy.data,p,q,qc,n,trans,add));return;}
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
    dy.write(initial);methods.push_back({{"precision",precision==0?"FP64":precision==1?"FP32_pedantic":precision==2?"TF32_requested":"FP32_fused"},{"accuracy",check},{"timing",timing(apply)},
      {"extra_fp32_workspace_bytes",precision==3?db.size*4:precision==0?0:(ni+no+db.size)*4}});
  }
  result["methods"]=methods;db.check();dx.check();dy.check();fb.check();fx.check();fy.check();result["canaries_passed"]=true;
  CEED(CeedVectorDestroy(&u));CEED(CeedVectorDestroy(&v));return result;
}

int main(int argc,char**argv){
  try{
    if(argc<2||argc>4)throw std::runtime_error("expected output path [scale] [fused]");
    bool scale=false,fused=false;
    for(int i=2;i<argc;++i){if(std::string(argv[i])=="scale"&&!scale)scale=true;
      else if(std::string(argv[i])=="fused"&&!fused)fused=true;else throw std::runtime_error("invalid/duplicate suite option");}
    if(palace_probe_fused_basis(nullptr,nullptr,nullptr,20,14,3,0,false,false)!=cudaErrorInvalidValue)
      throw std::runtime_error("fused argument guard failed");
    mfem::Mpi::Init(argc,argv);mfem::Device device("cpu");
    Ceed ceed;CEED(CeedInit("/gpu/cuda/magma",&ceed));cublasHandle_t handle;BLAS(cublasCreate(&handle));
    cudaDeviceProp prop;CUDA(cudaGetDeviceProperties(&prop,0));int blas_version;BLAS(cublasGetVersion(handle,&blas_version));
    json report={{"scope","Isolated GPU-resident basis actions; not UVM, solver speedup or RF qualification. TF32 request is not proof of Tensor Core instructions."},
      {"gpu",prop.name},{"cublas_version",blas_version},{"suite",scale?"scale":"screen"},{"fused",fused},{"rows",json::array()}};
    // MFEM caches tabulations by rule address: retain mapped rules until FE teardown.
    std::vector<std::unique_ptr<mfem::IntegrationRule>> mapped_rules;
    mfem::ND_FECollection nd(2,3),nd2(2,2);mfem::RT_FECollection rt(1,3);mfem::H1_FECollection h1(2,3);
    for(int family=0;family<4;++family)for(int points:{6,14}) {
      if(scale&&(family!=0||points!=14))continue;
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
      if(scale&&components!=1)continue;
      if(components==2&&!(family==0&&points==14))continue;
      palace::ceed::InitBasisFromRule(*fe,*ir,components,ceed,&basis);
      for(auto mode:{CEED_EVAL_INTERP,(family==0||family==3)?CEED_EVAL_CURL:family==1?CEED_EVAL_DIV:CEED_EVAL_GRAD})
        for(int elems:(scale?std::vector<int>{257,1023,4099,16383,65537,131071,1601320}:std::vector<int>{257,131071}))for(int variant=0;variant<3;++variant) {
          auto row=action(ceed,basis,handle,mode,elems,components,variant!=0,variant==2,fused);row["family"]=family;row["rule_degree"]=degree;
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
