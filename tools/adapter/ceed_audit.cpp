// SPDX-License-Identifier: Apache-2.0
// Opt-in host metadata only. No field copies, CUDA calls or arithmetic changes.
#include <ceed.h>
#include <ceed/backend.h>
#include <dlfcn.h>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <mutex>
#include <string_view>
#include <tuple>
#include "pc_basis.hpp"

namespace {
constexpr size_t max_groups = 2048;
using Key = std::tuple<int,int,int,int,int,int,int,int,int,int,long long,long long>;
struct Stats {
  std::mutex mutex;
  std::map<Key,unsigned long long> groups;
  unsigned long long calls=0, errors=0, overflow=0;
};
Stats &stats() { static auto *s=new Stats; return *s; }  // DSO-safe process lifetime.
bool enabled() {
  static const bool on=[] {const char *s=std::getenv("PALACE_CEED_BASIS_AUDIT");return s&&std::string_view(s)=="1";}();
  return on;
}
template<class T> T next(const char *name) {
  auto p=dlsym(RTLD_NEXT,name);
  if(!p){std::fprintf(stderr,"Basis audit: missing %s\n",name);std::abort();}
  return reinterpret_cast<T>(p);
}
void record(CeedBasis basis,CeedInt nelem,CeedTransposeMode transpose,CeedEvalMode mode,
            CeedVector u,CeedVector v,bool add,int result) {
  static_assert(sizeof(CeedScalar)==8,"Basis audit expects pinned FP64 libCEED ABI");
  static auto nodes=next<decltype(&CeedBasisGetNumNodes)>("CeedBasisGetNumNodes");
  static auto qpts=next<decltype(&CeedBasisGetNumQuadraturePoints)>("CeedBasisGetNumQuadraturePoints");
  static auto components=next<decltype(&CeedBasisGetNumComponents)>("CeedBasisGetNumComponents");
  static auto qcomponents=next<decltype(&CeedBasisGetNumQuadratureComponents)>("CeedBasisGetNumQuadratureComponents");
  static auto space=next<decltype(&CeedBasisGetFESpace)>("CeedBasisGetFESpace");
  static auto topology=next<decltype(&CeedBasisGetTopology)>("CeedBasisGetTopology");
  static auto length=next<decltype(&CeedVectorGetLength)>("CeedVectorGetLength");
  CeedInt p=0,q=0,c=0,qc=0;
  CeedFESpace fs;
  CeedElemTopology topo;
  CeedSize ul=0,vl=0;
  bool ok=result==0;
  // All getters inspect host metadata; do not request or copy any vector data.
  ok = ok && nodes(basis,&p)==0 && qpts(basis,&q)==0 && components(basis,&c)==0
       && qcomponents(basis,mode,&qc)==0 && space(basis,&fs)==0 && topology(basis,&topo)==0;
  if(u!=CEED_VECTOR_NONE) ok=ok&&length(u,&ul)==0;
  ok=ok&&length(v,&vl)==0;
  auto &s=stats();std::lock_guard<std::mutex> guard(s.mutex);
  ++s.calls;
  if(!ok){++s.errors;return;}
  Key key{int(topo),int(fs),p,q,c,qc,nelem,int(mode),int(transpose),int(add),ul,vl};
  auto it=s.groups.find(key);
  if(it==s.groups.end()) {
    if(s.groups.size()>=max_groups){++s.overflow;return;}
    it=s.groups.emplace(key,0).first;
  }
  ++it->second;
}
__attribute__((destructor)) void report() {
  if(!enabled())return;
  auto &s=stats();std::lock_guard<std::mutex> guard(s.mutex);
  for(const auto &[key,calls]:s.groups) {
    const auto [topo,fs,p,q,c,qc,nelem,mode,transpose,add,ul,vl]=key;
    std::fprintf(stderr,"PALACE_BASIS_AUDIT {\"topology\":%d,\"space\":%d,\"P\":%d,\"Q\":%d,\"components\":%d,\"q_components\":%d,\"elements\":%d,\"eval\":%d,\"transpose\":%d,\"add\":%d,\"input_length\":%lld,\"output_length\":%lld,\"scalar_bytes\":8,\"calls\":%llu}\n",
      topo,fs,p,q,c,qc,nelem,mode,transpose,add,ul,vl,calls);
  }
  std::fprintf(stderr,"PALACE_BASIS_AUDIT_END {\"groups\":%zu,\"calls\":%llu,\"errors\":%llu,\"overflow\":%llu}\n",
    s.groups.size(),s.calls,s.errors,s.overflow);
}
}

extern "C" int CeedBasisApply(CeedBasis basis,CeedInt nelem,CeedTransposeMode transpose,
                              CeedEvalMode mode,CeedVector u,CeedVector v) {
  static auto fn=next<decltype(&CeedBasisApply)>("CeedBasisApply");
  int result;
  if(!PalacePCBasisTryApply(basis,nelem,transpose,mode,u,v,false,&result))result=fn(basis,nelem,transpose,mode,u,v);
  if(enabled())record(basis,nelem,transpose,mode,u,v,false,result);
  return result;
}
extern "C" int CeedBasisApplyAdd(CeedBasis basis,CeedInt nelem,CeedTransposeMode transpose,
                                 CeedEvalMode mode,CeedVector u,CeedVector v) {
  static auto fn=next<decltype(&CeedBasisApplyAdd)>("CeedBasisApplyAdd");
  int result;
  if(!PalacePCBasisTryApply(basis,nelem,transpose,mode,u,v,true,&result))result=fn(basis,nelem,transpose,mode,u,v);
  if(enabled())record(basis,nelem,transpose,mode,u,v,true,result);
  return result;
}
