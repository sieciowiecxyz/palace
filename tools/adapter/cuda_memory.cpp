// CUDA UVM allocation experiment and cuDSS allocator accounting; host-only translation unit.
#include <cudss.h>
#include <cuda_runtime.h>
#include <dlfcn.h>
#include <execinfo.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <string_view>
#include <string>
#include <unordered_map>
#include <atomic>
#include <mutex>
#include <chrono>

extern "C" void PalaceProfileSynchronize() {
  int version;
  const auto marker=cudaRuntimeGetVersion(&version);
  if(marker!=cudaSuccess){std::fprintf(stderr,"Profile version marker failed\n");std::abort();}
  const auto begin=std::chrono::steady_clock::now().time_since_epoch();
  const auto error=cudaDeviceSynchronize();
  const auto end=std::chrono::steady_clock::now().time_since_epoch();
  if(error!=cudaSuccess){std::fprintf(stderr,"Profile window synchronization failed: %s\n",cudaGetErrorString(error));std::abort();}
  std::fprintf(stderr,"PALACE_PROFILE_SYNC {\"begin_ns\":%lld,\"end_ns\":%lld}\n",
               static_cast<long long>(std::chrono::duration_cast<std::chrono::nanoseconds>(begin).count()),
               static_cast<long long>(std::chrono::duration_cast<std::chrono::nanoseconds>(end).count()));
}

namespace {
std::atomic<uint64_t> dss_live{0}, dss_peak{0}, dss_allocations{0};
struct ManagedState {
  std::mutex mutex;
  std::once_flag reserve_once;
  std::unordered_map<void *,size_t> sizes;
  uint64_t live=0, peak=0, allocations=0, interval_peak=0;
  double marked_at=0;
  std::string phase="unmarked";
  void *reserve=nullptr;
  size_t reserved=0;
};
// Intentionally process-lifetime bookkeeping: other DSOs can free CUDA data
// during their destructors, after ordinary C++ static objects are destroyed.
ManagedState &managed_state() { static auto *s=new ManagedState; return *s; }
bool flag(const char *name) { const char *s=std::getenv(name); return s && std::string_view(s)=="1"; }
bool managed() { return flag("PALACE_CUDA_MANAGED"); }
bool hybrid() { return std::getenv("PALACE_CUDSS_HYBRID_MIB") != nullptr; }

template <typename T> T next(const char *name) {
  void *p = dlsym(RTLD_NEXT, name);
  if (!p) { std::fprintf(stderr, "FP32 shim: missing %s\n", name); std::abort(); }
  return reinterpret_cast<T>(p);
}
using Malloc = cudaError_t (*)(void **,size_t);
using ManagedMalloc = cudaError_t (*)(void **,size_t,unsigned int);
using Free = cudaError_t (*)(void *);
void reserve_memory() {
  auto &s=managed_state();
  std::call_once(s.reserve_once,[&] {
    const char *value=std::getenv("PALACE_CUDA_RESERVE_MIB");
    if (!value || !*value) return;
    char *end=nullptr; unsigned long long mib=std::strtoull(value,&end,10);
    if (*end || mib>8192) { std::fprintf(stderr,"Invalid UVM pressure reservation\n");std::abort(); }
    if(!mib)return;
    s.reserved=size_t(mib)*1024*1024;
    auto fn=next<Malloc>("cudaMalloc");
    if (fn(&s.reserve,s.reserved)!=cudaSuccess || cudaMemset(s.reserve,0,s.reserved)!=cudaSuccess) {
      std::fprintf(stderr,"Cannot reserve UVM pressure buffer\n");std::abort();
    }
    std::fprintf(stderr,"CUDA_UVM_PRESSURE: reserved_device_bytes=%zu\n",s.reserved);
  });
}
void trace_managed(const char *event, void *p, size_t n, uint64_t live) {
  if(!flag("PALACE_CUDA_ALLOC_TRACE") || n<16*1024*1024)return;
  auto t=std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
  std::fprintf(stderr,"PALACE_ALLOC {\"event\":\"%s\",\"kind\":\"managed\",\"pointer\":\"%p\",\"bytes\":%zu,\"logical_live_bytes\":%llu,\"t_s\":%.9f}\n",
               event,p,n,(unsigned long long)live,t);
  if(std::string_view(event)=="alloc") {
    void *frames[16];int count=backtrace(frames,16);
    char **names=backtrace_symbols(frames,count);
    if(names) {
      for(int i=0;i<count;i++)std::fprintf(stderr,"PALACE_ALLOC_STACK %p %d %s\n",p,i,names[i]);
      std::free(names);
    }
  }
}
void record_managed(void *p,size_t n) {
  auto &s=managed_state();std::lock_guard<std::mutex> guard(s.mutex);
  s.sizes[p]=n;s.live+=n;if(s.live>s.peak)s.peak=s.live;
  if(s.live>s.interval_peak)s.interval_peak=s.live;++s.allocations;
  trace_managed("alloc",p,n,s.live);
}
int dss_alloc(void *,void **p,size_t n,cudaStream_t) {
  // cuDSS owns host/device staging in hybrid mode: keep its device workspace
  // device-resident instead of layering demand-paged UVM on top of it.
  auto error=hybrid()?next<Malloc>("cudaMalloc")(p,n):cudaMalloc(p,n);
  if(error==cudaSuccess) {
    auto live=dss_live.fetch_add(n)+n;
    auto peak=dss_peak.load();while(live>peak && !dss_peak.compare_exchange_weak(peak,live)){}
    ++dss_allocations;
    if(flag("PALACE_CUDA_ALLOC_TRACE") && n>=16*1024*1024)
      std::fprintf(stderr,"CUDSS_ALLOC {\"bytes\":%zu,\"live_bytes\":%llu,\"peak_bytes\":%llu,\"managed\":%d}\n",
                   n,(unsigned long long)live,(unsigned long long)dss_peak.load(),int(managed()&&!hybrid()));
  }
  return int(error);
}
int dss_free(void *,void *p,size_t n,cudaStream_t) {
  auto error=cudaFree(p);if(error==cudaSuccess)dss_live.fetch_sub(n);return int(error);
}
__attribute__((destructor)) void report_memory() {
  if(dss_allocations) std::fprintf(stderr,
    "CUDSS_MEMORY: precision=%s managed=%d peak_bytes=%llu live_bytes=%llu allocations=%llu\n",
    flag("PALACE_CUDSS_FP32")?"fp32":"fp64",int(managed() && !hybrid()),(unsigned long long)dss_peak.load(),
    (unsigned long long)dss_live.load(),(unsigned long long)dss_allocations.load());
  if(managed()) {
    auto &s=managed_state();
    if(s.allocations || s.reserved)std::fprintf(stderr,"CUDA_UVM: peak_managed_bytes=%llu live_managed_bytes=%llu allocations=%llu reserved_device_bytes=%zu\n",
      (unsigned long long)s.peak,(unsigned long long)s.live,(unsigned long long)s.allocations,s.reserved);
    if(s.reserve)next<Free>("cudaFree")(s.reserve);
  }
}
}

extern "C" void PalaceMemoryMark(const char *label) {
  if(!flag("PALACE_MEMORY_MARKS") || !managed())return;
  auto &s=managed_state();std::lock_guard<std::mutex> guard(s.mutex);
  const auto now=std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
  // This records allocation lifetimes, not completion of asynchronous GPU work.
  std::fprintf(stderr,"PALACE_MEMORY_PHASE {\"from\":\"%s\",\"to\":\"%s\",\"t_s\":%.9f,\"elapsed_s\":%.9f,\"managed_live_bytes\":%llu,\"managed_interval_peak_bytes\":%llu,\"managed_process_peak_bytes\":%llu,\"cudss_live_bytes\":%llu}\n",
    s.phase.c_str(),label,now,s.marked_at?now-s.marked_at:0.0,
    (unsigned long long)s.live,(unsigned long long)s.interval_peak,
    (unsigned long long)s.peak,(unsigned long long)dss_live.load());
  s.phase=label;s.marked_at=now;s.interval_peak=s.live;
}

extern "C" cudssStatus_t cudssConfigCreate(cudssConfig_t *config) {
  static auto fn=next<decltype(&cudssConfigCreate)>("cudssConfigCreate");
  auto status=fn(config);
  if(status!=CUDSS_STATUS_SUCCESS)return status;
  if(flag("PALACE_CUDSS_HYBRID_EXECUTE")) {
    if(hybrid()) {
      std::fprintf(stderr,"Hybrid execute and hybrid memory cannot be combined in this profile.\n");
      cudssConfigDestroy(*config);return CUDSS_STATUS_INVALID_VALUE;
    }
    int enabled=1;
    status=cudssConfigSet(*config,CUDSS_CONFIG_HYBRID_EXECUTE_MODE,&enabled,sizeof(enabled));
    if(status!=CUDSS_STATUS_SUCCESS)cudssConfigDestroy(*config);
    else std::fprintf(stderr,"CUDSS_HYBRID_EXECUTE: enabled=1\n");
    return status;
  }
  if(!hybrid())return status;
  char *end=nullptr;
  auto mib=std::strtoull(std::getenv("PALACE_CUDSS_HYBRID_MIB"),&end,10);
  if(*end || mib<256 || mib>16384) {
    std::fprintf(stderr,"Invalid PALACE_CUDSS_HYBRID_MIB (256..16384)\n");std::abort();
  }
  int mode=1;
  int64_t bytes=int64_t(mib)*1024*1024;
  status=cudssConfigSet(*config,CUDSS_CONFIG_HYBRID_MODE,&mode,sizeof(mode));
  if(status==CUDSS_STATUS_SUCCESS)
    status=cudssConfigSet(*config,CUDSS_CONFIG_HYBRID_DEVICE_MEMORY_LIMIT,&bytes,sizeof(bytes));
  if(status!=CUDSS_STATUS_SUCCESS)cudssConfigDestroy(*config);
  else std::fprintf(stderr,"CUDSS_HYBRID: device_limit_bytes=%lld; device_workspace_not_UVM\n",(long long)bytes);
  return status;
}

extern "C" cudaError_t cudaMallocManaged(void **p,size_t n,unsigned int flags) {
  static auto fn=next<ManagedMalloc>("cudaMallocManaged");
  if(managed())reserve_memory();
  auto error=fn(p,n,flags);if(error==cudaSuccess && managed())record_managed(*p,n);return error;
}
extern "C" cudaError_t cudaMalloc(void **p,size_t n) {
  static auto fn=next<Malloc>("cudaMalloc");
  if(!managed() || !n)return fn(p,n);
  return cudaMallocManaged(p,n,cudaMemAttachGlobal);
}
extern "C" cudaError_t cudaFree(void *p) {
  static auto fn=next<Free>("cudaFree");
  auto error=fn(p);
  if(error==cudaSuccess && managed()) {
    auto &s=managed_state();std::lock_guard<std::mutex> guard(s.mutex);
    auto it=s.sizes.find(p);if(it!=s.sizes.end()){s.live-=it->second;trace_managed("free",p,it->second,s.live);s.sizes.erase(it);}
  }
  return error;
}
extern "C" cudssStatus_t cudssCreate(cudssHandle_t *h) {
  static auto fn=next<decltype(&cudssCreate)>("cudssCreate");
  auto status=fn(h);
  if(status==CUDSS_STATUS_SUCCESS && (managed() || flag("PALACE_CUDSS_TRACK"))) {
    cudssDeviceMemHandler_t handler{};
    handler.device_alloc=dss_alloc;handler.device_free=dss_free;
    std::snprintf(handler.name,sizeof(handler.name),"Palace tracked%s",managed()?" UVM":"");
    status=cudssSetDeviceMemHandler(*h,&handler);
    if(status!=CUDSS_STATUS_SUCCESS)cudssDestroy(*h);
  }
  return status;
}

// MFEM's static cudart calls do not traverse the dynamic cudaMalloc interposer.
// Keep its DEVICE memory-manager metadata intact: MFEM_MEMORY=uvm has an
// Unknown-pointer failure in this pinned runtime. Replace only actual allocation.
namespace mfem {
void *CuMemAlloc(void **p,size_t n) {
  using Fn=void *(*)(void **,size_t);
  static auto fn=next<Fn>("_ZN4mfem10CuMemAllocEPPvm");
  if(!managed())return fn(p,n);
  auto error=cudaMalloc(p,n);
  if(error!=cudaSuccess){std::fprintf(stderr,"MFEM managed allocation failed: %s\n",cudaGetErrorString(error));std::abort();}
  return *p;
}
void *CuMemFree(void *p) {
  using Fn=void *(*)(void *);
  static auto fn=next<Fn>("_ZN4mfem9CuMemFreeEPv");
  if(!managed())return fn(p);
  auto error=cudaFree(p);
  if(error!=cudaSuccess){std::fprintf(stderr,"MFEM managed free failed: %s\n",cudaGetErrorString(error));std::abort();}
  return p;
}
}
