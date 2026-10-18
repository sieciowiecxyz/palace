// SPDX-License-Identifier: Apache-2.0
// Two operators, passive-state changes and diagonal/ApplyAdd alternation.
#include <ceed.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "ceed_qpool_probe.h"
#define CHECK(call) do { int error = (call); if (error) { fprintf(stderr, "probe error %d: %s\n", error, #call); return 1; } } while (0)

static int verify(CeedVector vector, double even, double odd, int diagonal) {
  const CeedScalar *values;
  CHECK(CeedVectorGetArrayRead(vector, CEED_MEM_HOST, &values));
  for (int i = 0; i < 6; i++) {
    double expected = (i % 2 ? odd : even) * (diagonal ? 1 : i+1);
    if (!isfinite(values[i]) || fabs(values[i]-expected) > 1e-11) {
      fprintf(stderr, "probe mismatch %d: %.17g expected %.17g\n", i, values[i], expected);
      return 1;
    }
  }
  CHECK(CeedVectorRestoreArrayRead(vector, &values));
  return 0;
}

int main(void) {
  Ceed ceed;
  CeedBasis identity, scaled;
  CeedElemRestriction restriction;
  CeedQFunction qf;
  CeedOperator a, b;
  CeedVector x, y, diag, ca, cb;
  const CeedInt offsets[] = {0,1,2,3,4,5};
  const CeedScalar input[] = {1,2,3,4,5,6};
  const CeedScalar interp_i[] = {1,0,0,1}, interp_b[] = {2,0,0,3};
  const CeedScalar grad[] = {0,0,0,0}, points[] = {-0.5773502691896257,0.5773502691896257}, weights[] = {1,1};
  CHECK(CeedInit("/gpu/cuda/magma", &ceed));
  CHECK(CeedBasisCreateH1(ceed, CEED_TOPOLOGY_LINE, 1, 2, 2, interp_i, grad, points, weights, &identity));
  CHECK(CeedBasisCreateH1(ceed, CEED_TOPOLOGY_LINE, 1, 2, 2, interp_b, grad, points, weights, &scaled));
  CHECK(CeedElemRestrictionCreate(ceed, 3, 2, 1, 1, 6, CEED_MEM_HOST, CEED_COPY_VALUES, offsets, &restriction));
  CHECK(CeedQFunctionCreateInterior(ceed, 1, PalacePoolMass,
        "/src/palace/tools/experiments/ceed_qpool_probe.h:PalacePoolMass", &qf));
  CHECK(CeedQFunctionAddInput(qf, "u", 1, CEED_EVAL_INTERP));
  CHECK(CeedQFunctionAddInput(qf, "coefficient", 1, CEED_EVAL_INTERP));
  CHECK(CeedQFunctionAddOutput(qf, "v", 1, CEED_EVAL_INTERP));
  CHECK(CeedVectorCreate(ceed, 6, &x)); CHECK(CeedVectorCreate(ceed, 6, &y));
  CHECK(CeedVectorCreate(ceed, 6, &diag)); CHECK(CeedVectorCreate(ceed, 6, &ca));
  CHECK(CeedVectorCreate(ceed, 6, &cb));
  CHECK(CeedVectorSetArray(x, CEED_MEM_HOST, CEED_COPY_VALUES, (CeedScalar *)input));
  CHECK(CeedVectorSetValue(ca, 2)); CHECK(CeedVectorSetValue(cb, 3));
  CHECK(CeedOperatorCreate(ceed, qf, CEED_QFUNCTION_NONE, CEED_QFUNCTION_NONE, &a));
  CHECK(CeedOperatorSetField(a, "u", restriction, identity, CEED_VECTOR_ACTIVE));
  CHECK(CeedOperatorSetField(a, "coefficient", restriction, identity, ca));
  CHECK(CeedOperatorSetField(a, "v", restriction, identity, CEED_VECTOR_ACTIVE));
  CHECK(CeedOperatorCreate(ceed, qf, CEED_QFUNCTION_NONE, CEED_QFUNCTION_NONE, &b));
  CHECK(CeedOperatorSetField(b, "u", restriction, scaled, CEED_VECTOR_ACTIVE));
  CHECK(CeedOperatorSetField(b, "coefficient", restriction, identity, cb));
  CHECK(CeedOperatorSetField(b, "v", restriction, scaled, CEED_VECTOR_ACTIVE));
  for (int repetition = 0; repetition < 4; repetition++) {
    double alpha = repetition < 2 ? 2 : 5;
    CHECK(CeedVectorSetValue(ca, alpha));
    CHECK(CeedOperatorApply(a, x, y, CEED_REQUEST_IMMEDIATE)); CHECK(verify(y, alpha, alpha, 0));
    CHECK(CeedOperatorApply(b, x, y, CEED_REQUEST_IMMEDIATE)); CHECK(verify(y, 12, 27, 0));
    CHECK(CeedOperatorLinearAssembleDiagonal(a, diag, CEED_REQUEST_IMMEDIATE)); CHECK(verify(diag, alpha, alpha, 1));
    CHECK(CeedOperatorLinearAssembleDiagonal(b, diag, CEED_REQUEST_IMMEDIATE)); CHECK(verify(diag, 12, 27, 1));
    CHECK(CeedOperatorApply(a, x, y, CEED_REQUEST_IMMEDIATE));
    CHECK(CeedOperatorApplyAdd(b, x, y, CEED_REQUEST_IMMEDIATE)); CHECK(verify(y, alpha+12, alpha+27, 0));
  }
  CHECK(CeedOperatorDestroy(&a)); CHECK(CeedOperatorDestroy(&b));
  CHECK(CeedVectorDestroy(&x)); CHECK(CeedVectorDestroy(&y)); CHECK(CeedVectorDestroy(&diag));
  CHECK(CeedVectorDestroy(&ca)); CHECK(CeedVectorDestroy(&cb));
  CHECK(CeedQFunctionDestroy(&qf)); CHECK(CeedElemRestrictionDestroy(&restriction));
  CHECK(CeedBasisDestroy(&identity)); CHECK(CeedBasisDestroy(&scaled)); CHECK(CeedDestroy(&ceed));
  puts("PALACE_QPOOL_PROBE: PASS two operators, passive updates, diagonal, ApplyAdd");
  return 0;
}
