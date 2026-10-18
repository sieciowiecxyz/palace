// Actual cuDSS regression: two RHS, descriptor updates, refactorization and cleanup.
#include <cudss.h>
#include <cuda_runtime.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#define CUDA(call) do { if ((call)!=cudaSuccess) return 2; } while(0)
#define DSS(call) do { if ((call)!=CUDSS_STATUS_SUCCESS) return 3; } while(0)
int main() {
  const int n=3, nnz=7, nrhs=2;
  int rows[]={0,2,5,7}, cols[]={0,1,0,1,2,1,2};
  double values[]={4.123456789,.2,.2,3.234567891,.3,.3,2.345678912};
  double exact[]={1.1,-2.2,3.3,-.7,.9,1.2}, rhs[6], result[6];
  int *ri,*ci; double *av,*bv,*xv;
  CUDA(cudaMalloc((void**)&ri,sizeof(rows))); CUDA(cudaMalloc((void**)&ci,sizeof(cols)));
  CUDA(cudaMalloc((void**)&av,sizeof(values))); CUDA(cudaMalloc((void**)&bv,sizeof(rhs)));
  CUDA(cudaMalloc((void**)&xv,sizeof(result)));
  CUDA(cudaMemcpy(ri,rows,sizeof(rows),cudaMemcpyHostToDevice));
  CUDA(cudaMemcpy(ci,cols,sizeof(cols),cudaMemcpyHostToDevice));
  cudssHandle_t h; cudssConfig_t cfg; cudssData_t data; cudssMatrix_t a,b,x;
  DSS(cudssCreate(&h)); DSS(cudssConfigCreate(&cfg)); DSS(cudssDataCreate(h,&data));
  DSS(cudssMatrixCreateCsr(&a,n,n,nnz,ri,nullptr,ci,av,CUDA_R_32I,CUDA_R_64F,
    CUDSS_MTYPE_SPD,CUDSS_MVIEW_FULL,CUDSS_BASE_ZERO));
  DSS(cudssMatrixCreateDn(&b,n,nrhs,n,bv,CUDA_R_64F,CUDSS_LAYOUT_COL_MAJOR));
  DSS(cudssMatrixCreateDn(&x,n,nrhs,n,xv,CUDA_R_64F,CUDSS_LAYOUT_COL_MAJOR));
  double maximum=0;
  for (int repeat=0;repeat<2;++repeat) {
    if (repeat) values[0]+=.4;
    for (int k=0;k<nrhs;++k) for (int i=0;i<n;++i) {
      rhs[k*n+i]=0; for (int j=rows[i];j<rows[i+1];++j) rhs[k*n+i]+=values[j]*exact[k*n+cols[j]];
    }
    CUDA(cudaMemcpy(av,values,sizeof(values),cudaMemcpyHostToDevice));
    CUDA(cudaMemcpy(bv,rhs,sizeof(rhs),cudaMemcpyHostToDevice));
    DSS(cudssMatrixSetValues(a,av)); DSS(cudssMatrixSetValues(b,bv)); DSS(cudssMatrixSetValues(x,xv));
    if (!repeat) DSS(cudssExecute(h,CUDSS_PHASE_ANALYSIS,cfg,data,a,x,b));
    DSS(cudssExecute(h,CUDSS_PHASE_FACTORIZATION,cfg,data,a,x,b));
    DSS(cudssExecute(h,CUDSS_PHASE_SOLVE,cfg,data,a,x,b));
    CUDA(cudaMemcpy(result,xv,sizeof(result),cudaMemcpyDeviceToHost));
    for (int i=0;i<n*nrhs;++i) maximum=std::fmax(maximum,std::fabs(result[i]-exact[i]));
  }
  DSS(cudssMatrixDestroy(a)); DSS(cudssMatrixDestroy(b)); DSS(cudssMatrixDestroy(x));
  DSS(cudssDataDestroy(h,data)); DSS(cudssConfigDestroy(cfg)); DSS(cudssDestroy(h));
  CUDA(cudaFree(ri)); CUDA(cudaFree(ci)); CUDA(cudaFree(av)); CUDA(cudaFree(bv)); CUDA(cudaFree(xv));
  std::printf("{\"two_rhs_refactor_max_error\":%.17g}\n",maximum);
  return maximum<2e-6 ? 0:4;
}
