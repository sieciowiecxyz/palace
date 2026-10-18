// Experimental libCEED active-Q workspace pool. Same pinned FP64 kernels.
// The generated translation unit retains libCEED's BSD-2-Clause header.
#include <dlfcn.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>

static _Atomic unsigned long palace_pool_calls, palace_pool_borrows;
static atomic_flag palace_pool_in_use = ATOMIC_FLAG_INIT;

static int PalaceQPoolBorrow(Ceed ceed, CeedOperatorField *fields,
                            CeedQFunctionField *qfields, CeedInt count,
                            CeedVector *vectors, CeedVector *saved) {
  for (CeedInt i = 0; i < count; i++) {
    CeedVector field;
    CeedEvalMode mode;
    CeedSize length;
    CeedCallBackend(CeedOperatorFieldGetVector(fields[i], &field));
    bool active = field == CEED_VECTOR_ACTIVE;
    CeedCallBackend(CeedVectorDestroy(&field));
    CeedCallBackend(CeedQFunctionFieldGetEvalMode(qfields[i], &mode));
    // Passive cached values and EVAL_NONE borrowed arrays remain untouched.
    if (!active || mode == CEED_EVAL_NONE || mode == CEED_EVAL_WEIGHT) continue;
    CeedCallBackend(CeedVectorGetLength(vectors[i], &length));
    saved[i] = vectors[i];
    CeedCallBackend(CeedGetWorkVector(ceed, length, &vectors[i]));
    atomic_fetch_add(&palace_pool_borrows, 1);
  }
  return CEED_ERROR_SUCCESS;
}

static int PalaceQPoolReturn(Ceed ceed, CeedInt count, CeedVector *vectors,
                            CeedVector *saved) {
  for (CeedInt i = 0; i < count; i++) {
    if (!saved[i]) continue;
    CeedCallBackend(CeedRestoreWorkVector(ceed, &vectors[i]));
    vectors[i] = saved[i];
  }
  return CEED_ERROR_SUCCESS;
}

__attribute__((destructor)) static void PalaceQPoolReport(void) {
  fprintf(stderr, "PALACE_CEED_QPOOL: calls=%lu borrowed_vectors=%lu sync=device-before-and-after FP64 RAM/VRAM only\n",
          atomic_load(&palace_pool_calls),
          atomic_load(&palace_pool_borrows));
}
