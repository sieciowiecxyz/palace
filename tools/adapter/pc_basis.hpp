// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <ceed.h>
// false means the original public libCEED apply must run; no arithmetic changed.
extern "C" bool PalacePCBasisTryApply(CeedBasis,CeedInt,CeedTransposeMode,CeedEvalMode,
                                     CeedVector,CeedVector,bool,int*);
