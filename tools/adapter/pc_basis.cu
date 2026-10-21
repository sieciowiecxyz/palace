// SPDX-License-Identifier: Apache-2.0
#include "pc_basis.hpp"
#include "ceed_fused.cuh"
#include <ceed/backend.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <map>
#include <mutex>
#include <string_view>
#include <tuple>
#include <vector>

namespace {
bool enabled(){static const bool on=[] {auto s=std::getenv("PALACE_PC_BASIS_FP32_FORWARD");return s&&std::string_view(s)=="1";}();return on;}
thread_local unsigned depth=0;
using Key=std::tuple<int,int,int,std::vector<double>>;
struct Table {float *data;size_t bytes;};
struct State {
  std::mutex mutex;std::map<Key,Table> tables;
  unsigned long long enters=0,exits=0,active=0,mixed=0,pc_original=0,outside_original=0,
                     transpose_original=0,alias_original=0,capacity_original=0,misses=0,hits=0,
                     allocated=0,freed=0,releases=0;
  bool closed=false;
};
State &state(){static auto *s=new State;return *s;}
[[noreturn]] void fail(const char *message){std::fprintf(stderr,"PALACE_PC_BASIS_ERROR %s\n",message);std::abort();}
void check(int code){if(code)fail("libCEED metadata/vector error");}
void cuda_check(cudaError_t error){if(error!=cudaSuccess)fail(cudaGetErrorString(error));}
bool supported(int p,int q,int qc){return
  (p==20&&(q==6||q==14)&&qc==3)||
  ((p==15||p==10)&&(q==6||q==14)&&(qc==1||qc==3))||
  (p==8&&q==6&&(qc==1||qc==2));}

__attribute__((destructor)) void report(){
  if(!enabled())return;
  auto &s=state();std::lock_guard<std::mutex> lock(s.mutex);
  std::fprintf(stderr,"PALACE_PC_BASIS_END {\"enters\":%llu,\"exits\":%llu,\"active\":%llu,\"mixed_forward\":%llu,\"pc_original\":%llu,\"outside_original\":%llu,\"transpose_original\":%llu,\"alias_original\":%llu,\"capacity_original\":%llu,\"cache_misses\":%llu,\"cache_hits\":%llu,\"allocated_bytes\":%llu,\"freed_bytes\":%llu,\"live_bytes\":%llu,\"releases\":%llu,\"closed\":%s,\"min_N\":8192,\"scalar_bytes\":8}\n",
    s.enters,s.exits,s.active,s.mixed,s.pc_original,s.outside_original,s.transpose_original,
    s.alias_original,s.capacity_original,s.misses,s.hits,s.allocated,s.freed,s.allocated-s.freed,s.releases,s.closed?"true":"false");
}
}

extern "C" void PalacePCBasisScope(int begin){
  if(!enabled())return;
  auto &s=state();std::lock_guard<std::mutex> lock(s.mutex);
  if(begin==1){if(s.closed)fail("PC scope after final release");++depth;++s.active;++s.enters;}
  else if(begin==0){if(!depth||!s.active)fail("unbalanced PC scope");--depth;--s.active;++s.exits;}
  else fail("invalid PC scope hook");
}

extern "C" void PalacePCBasisRelease(){
  if(!enabled())return;
  auto &s=state();std::lock_guard<std::mutex> lock(s.mutex);
  if(s.active||depth||s.closed)fail("invalid PC basis release lifetime");
  cuda_check(cudaDeviceSynchronize());
  for(auto &[key,table]:s.tables){cuda_check(cudaFree(table.data));s.freed+=table.bytes;}
  s.tables.clear();s.closed=true;++s.releases;
}

extern "C" bool PalacePCBasisTryApply(CeedBasis basis,CeedInt nelem,CeedTransposeMode transpose,
                                      CeedEvalMode mode,CeedVector u,CeedVector v,bool add,int *result){
  if(!enabled())return false;
  auto &s=state();std::lock_guard<std::mutex> lock(s.mutex);
  if(!depth){++s.outside_original;return false;}
  auto original=[&]{++s.pc_original;return false;};
  if(transpose==CEED_TRANSPOSE){++s.transpose_original;return original();}
  if(add||transpose!=CEED_NOTRANSPOSE||nelem<=0||u==CEED_VECTOR_NONE||u==v
      ||(mode!=CEED_EVAL_INTERP&&mode!=CEED_EVAL_GRAD&&mode!=CEED_EVAL_CURL&&mode!=CEED_EVAL_DIV))return original();
  bool tensor;check(CeedBasisIsTensor(basis,&tensor));if(tensor)return original();
  CeedInt p,q,c,qc;check(CeedBasisGetNumNodes(basis,&p));check(CeedBasisGetNumQuadraturePoints(basis,&q));
  check(CeedBasisGetNumComponents(basis,&c));check(CeedBasisGetNumQuadratureComponents(basis,mode,&qc));
  const long long wide_n=static_cast<long long>(nelem)*c;
  if(!supported(p,q,qc)||wide_n<8192||wide_n>std::numeric_limits<int>::max()/std::max(p,q*qc))return original();
  const int n=int(wide_n);const size_t ni=size_t(n)*p,no=size_t(n)*q*qc;
  CeedSize ul,vl;check(CeedVectorGetLength(u,&ul));check(CeedVectorGetLength(v,&vl));
  if(ul<0||vl<0||size_t(ul)<ni||size_t(vl)<no)fail("short basis vector");
  const double *coefficients=nullptr;
  if(mode==CEED_EVAL_INTERP)check(CeedBasisGetInterp(basis,&coefficients));
  else if(mode==CEED_EVAL_GRAD)check(CeedBasisGetGrad(basis,&coefficients));
  else if(mode==CEED_EVAL_CURL)check(CeedBasisGetCurl(basis,&coefficients));
  else check(CeedBasisGetDiv(basis,&coefficients));
  if(!coefficients)fail("missing basis coefficients");
  std::vector<double> values(coefficients,coefficients+p*q*qc);
  for(double value:values)if(!std::isfinite(value)||!std::isfinite(float(value)))return original();
  Key key{p,q,qc,std::move(values)};auto it=s.tables.find(key);
  if(it==s.tables.end()){
    if(s.tables.size()>=256){++s.capacity_original;return original();}
    const auto &host=std::get<3>(key);std::vector<float> packed(host.begin(),host.end());
    Table table{nullptr,packed.size()*sizeof(float)};
    cuda_check(cudaMalloc(&table.data,table.bytes));
    cuda_check(cudaMemcpy(table.data,packed.data(),table.bytes,cudaMemcpyHostToDevice));
    s.allocated+=table.bytes;++s.misses;it=s.tables.emplace(std::move(key),table).first;
  }else ++s.hits;
  const double *input=nullptr;double *output=nullptr;
  check(CeedVectorGetArrayRead(u,CEED_MEM_DEVICE,&input));
  check(CeedVectorGetArrayWrite(v,CEED_MEM_DEVICE,&output));
  const auto a=reinterpret_cast<std::uintptr_t>(input),b=reinterpret_cast<std::uintptr_t>(output);
  if(a<b+no*sizeof(double)&&b<a+ni*sizeof(double)){
    check(CeedVectorRestoreArray(v,&output));check(CeedVectorRestoreArrayRead(u,&input));
    ++s.alias_original;return original();
  }
  // Conservative cross-backend stream safety, matching synchronous basis semantics.
  cuda_check(cudaDeviceSynchronize());
  cuda_check(palace_pc_basis::Apply(it->second.data,input,output,p,q,qc,n,false,false));
  cuda_check(cudaDeviceSynchronize());
  check(CeedVectorRestoreArray(v,&output));check(CeedVectorRestoreArrayRead(u,&input));
  ++s.mixed;*result=0;return true;
}
