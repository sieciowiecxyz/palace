// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_LINALG_MIXEDBASIS_HPP
#define PALACE_LINALG_MIXEDBASIS_HPP

// Arithmetic shared by the isolated CUDA probe and the future MFEM adapter.
// No allocation, reduction backend, MPI, or solver policy is hidden here.
#if defined(__CUDACC__) || defined(__HIPCC__)
#define PALACE_MIXED_HD __host__ __device__
#else
#define PALACE_MIXED_HD
#endif

namespace palace::mixed_basis
{
struct Pair
{
  double real, imag;
};

template <typename Storage>
PALACE_MIXED_HD inline double DotRealPart(int start, int stride, int n,
                                         const Storage *basis, const double *full)
{
  double value = 0.0;
  for (int i = start; i < n; i += stride)
  {
    value += static_cast<double>(basis[i]) * full[i];
  }
  return value;
}

// Palace LocalDot(w,b) = sum(w * conj(b)), linear in its first argument.
// Both products and sums are double, even when Storage is float.
template <typename Storage>
PALACE_MIXED_HD inline Pair DotPart(int start, int stride, int n,
                                   const Storage *br, const Storage *bi,
                                   const double *wr, const double *wi)
{
  Pair value{0.0, 0.0};
  for (int i = start; i < n; i += stride)
  {
    const double r = static_cast<double>(br[i]), s = static_cast<double>(bi[i]);
    value.real += wr[i] * r + wi[i] * s;
    value.imag += wi[i] * r - wr[i] * s;
  }
  return value;
}

template <typename Storage>
PALACE_MIXED_HD inline void AddEntry(int i, const Storage *br, const Storage *bi,
                                    double ar, double ai, double *wr, double *wi)
{
  const double r = static_cast<double>(br[i]), s = static_cast<double>(bi[i]);
  wr[i] += ar * r - ai * s;
  wi[i] += ar * s + ai * r;
}
}  // namespace palace::mixed_basis

#undef PALACE_MIXED_HD
#endif
