// SPDX-License-Identifier: Apache-2.0
// Optional isolated cuBLASLt plan; no change to the Palace operator.
#include <cublasLt.h>
#include <cstdint>

struct LtBasisPlan {
  static constexpr size_t workspace_limit=64*1024*1024;
  cublasLtHandle_t handle=nullptr;
  cublasLtMatmulDesc_t desc=nullptr;
  cublasLtMatrixLayout_t a=nullptr,b=nullptr,c=nullptr;
  cublasLtMatmulPreference_t preference=nullptr;
  cublasLtMatmulAlgo_t algo{};
  json metadata;
  bool supported=false;
  static uint32_t alignment(const void *p) {
    auto value=reinterpret_cast<uintptr_t>(p);uint32_t result=1;
    while(result<256 && value%(result*2)==0)result*=2;
    return result;
  }
  LtBasisPlan(int p,int q,int n,bool trans,const float *av,const float *bv,float *cv) {
    BLAS(cublasLtCreate(&handle));
    BLAS(cublasLtMatmulDescCreate(&desc,CUBLAS_COMPUTE_32F_FAST_TF32,CUDA_R_32F));
    auto op=trans?CUBLAS_OP_N:CUBLAS_OP_T;
    BLAS(cublasLtMatmulDescSetAttribute(desc,CUBLASLT_MATMUL_DESC_TRANSA,&op,sizeof(op)));
    BLAS(cublasLtMatrixLayoutCreate(&a,CUDA_R_32F,p,q,p));
    BLAS(cublasLtMatrixLayoutCreate(&b,CUDA_R_32F,trans?q:p,n,trans?q:p));
    BLAS(cublasLtMatrixLayoutCreate(&c,CUDA_R_32F,trans?p:q,n,trans?p:q));
    BLAS(cublasLtMatmulPreferenceCreate(&preference));
    const size_t bytes=workspace_limit;
    BLAS(cublasLtMatmulPreferenceSetAttribute(preference,CUBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES,&bytes,sizeof(bytes)));
    const uint32_t alignments[]={alignment(av),alignment(bv),alignment(cv),alignment(cv)};
    const cublasLtMatmulPreferenceAttributes_t attributes[]={CUBLASLT_MATMUL_PREF_MIN_ALIGNMENT_A_BYTES,
      CUBLASLT_MATMUL_PREF_MIN_ALIGNMENT_B_BYTES,CUBLASLT_MATMUL_PREF_MIN_ALIGNMENT_C_BYTES,CUBLASLT_MATMUL_PREF_MIN_ALIGNMENT_D_BYTES};
    for(int i=0;i<4;++i)BLAS(cublasLtMatmulPreferenceSetAttribute(preference,attributes[i],&alignments[i],sizeof(uint32_t)));
    cublasLtMatmulHeuristicResult_t choices[8];int count=0;
    const auto status=cublasLtMatmulAlgoGetHeuristic(handle,desc,a,b,c,c,preference,8,choices,&count);
    metadata={{"heuristic_status",int(status)},{"returned",count},{"candidates",json::array()},
      {"tensor_op_mask",uint64_t(CUBLASLT_NUMERICAL_IMPL_FLAGS_TENSOR_OP_MASK)},
      {"tf32_input_mask",uint64_t(CUBLASLT_NUMERICAL_IMPL_FLAGS_INPUT_TF32)},
      {"alignment_bytes",{alignments[0],alignments[1],alignments[2],alignments[3]}},
      {"selection","first checked heuristic with TF32 input and tensor-op implementation; not exhaustive tuning"}};
    if(status==CUBLAS_STATUS_NOT_SUPPORTED)return;
    BLAS(status);
    for(int i=0;i<count;++i) {
      uint64_t flags=0;size_t written=0;int id=-1;
      cublasLtMatmulHeuristicResult_t checked{};
      checked.state=CUBLAS_STATUS_NOT_SUPPORTED;
      auto checked_status=CUBLAS_STATUS_NOT_SUPPORTED;
      // Other result fields are only valid when the heuristic state is success.
      if(choices[i].state==CUBLAS_STATUS_SUCCESS){
        BLAS(cublasLtMatmulAlgoCapGetAttribute(&choices[i].algo,CUBLASLT_ALGO_CAP_NUMERICAL_IMPL_FLAGS,&flags,sizeof(flags),&written));
        if(written!=sizeof(flags))throw std::runtime_error("Lt flags size");
        BLAS(cublasLtMatmulAlgoConfigGetAttribute(&choices[i].algo,CUBLASLT_ALGO_CONFIG_ID,&id,sizeof(id),&written));
        if(written!=sizeof(id))throw std::runtime_error("Lt algorithm ID size");
        checked_status=cublasLtMatmulAlgoCheck(handle,desc,a,b,c,c,&choices[i].algo,&checked);
      }
      const bool eligible=choices[i].state==CUBLAS_STATUS_SUCCESS && checked_status==CUBLAS_STATUS_SUCCESS &&
        checked.state==CUBLAS_STATUS_SUCCESS && checked.workspaceSize<=workspace_limit &&
        (flags&CUBLASLT_NUMERICAL_IMPL_FLAGS_TENSOR_OP_MASK) && (flags&CUBLASLT_NUMERICAL_IMPL_FLAGS_INPUT_TF32);
      metadata["candidates"].push_back({{"rank",i},{"id",id},{"impl_flags",flags},{"heuristic_state",int(choices[i].state)},
        {"check_status",int(checked_status)},{"check_state",int(checked.state)},
        {"workspace_bytes",checked.workspaceSize},{"eligible",eligible}});
      if(eligible&&!supported){algo=choices[i].algo;supported=true;metadata["selected_rank"]=i;metadata["selected_id"]=id;
        metadata["selected_impl_flags"]=flags;metadata["selected_workspace_bytes"]=checked.workspaceSize;}
    }
  }
  void apply(const float *av,const float *bv,float *cv,float beta,void *workspace) {
    if(!supported)throw std::runtime_error("unsupported Lt plan");
    const float alpha=1;
    BLAS(cublasLtMatmul(handle,desc,&alpha,av,a,bv,b,&beta,cv,c,cv,c,&algo,workspace,workspace_limit,0));
  }
  ~LtBasisPlan(){if(preference)cublasLtMatmulPreferenceDestroy(preference);if(c)cublasLtMatrixLayoutDestroy(c);
    if(b)cublasLtMatrixLayoutDestroy(b);if(a)cublasLtMatrixLayoutDestroy(a);
    if(desc)cublasLtMatmulDescDestroy(desc);if(handle)cublasLtDestroy(handle);}
  LtBasisPlan(const LtBasisPlan&)=delete;
};
