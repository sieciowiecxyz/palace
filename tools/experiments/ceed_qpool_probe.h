// SPDX-License-Identifier: Apache-2.0
#include <ceed/types.h>
CEED_QFUNCTION(PalacePoolMass)(void *ctx, CeedInt Q, const CeedScalar *const *in,
                              CeedScalar *const *out) {
  const CeedScalar *u = in[0], *coefficient = in[1];
  CeedScalar *v = out[0];
  for (CeedInt q = 0; q < Q; q++) v[q] = coefficient[q] * u[q];
  return 0;
}
