// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_LINALG_MIXEDCOARSE_HPP
#define PALACE_LINALG_MIXEDCOARSE_HPP

#include <climits>
#include <cmath>
#include <cuComplex.h>
#include <cuda_runtime.h>

namespace palace::mixedcoarse
{
// Missing/zero diagonal uses the row maximum; an empty/nonfinite row is invalid.
inline double Scale(double diagonal, double row_max)
{
  const double magnitude = diagonal > 0.0 ? diagonal : row_max;
  return std::isfinite(diagonal) && std::isfinite(row_max) && magnitude > 0.0
             ? 1.0 / std::sqrt(magnitude) : 0.0;
}
// Interleaved complex vectors, column-major RHS, zero-based CSR. Caller owns
// finite/scaling/CSR validation and stream ordering. No extra storage or host copy.
__global__ inline void PackKernel(int n, int total, const double *d,
                                 const cuDoubleComplex *x, cuComplex *y, int *invalid)
{
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < total)
  {
    y[i] = make_cuComplex(float(d[i % n] * x[i].x), float(d[i % n] * x[i].y));
    if (invalid && (!isfinite(y[i].x) || !isfinite(y[i].y))) atomicExch(invalid, 1);
  }
}

__global__ inline void AccumulateKernel(int n, int total, const double *d,
                                       const cuComplex *x, cuDoubleComplex *y, bool add)
{
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < total)
  {
    const double r = d[i % n] * double(x[i].x), im = d[i % n] * double(x[i].y);
    y[i] = add ? make_cuDoubleComplex(y[i].x + r, y[i].y + im) : make_cuDoubleComplex(r, im);
  }
}

__global__ inline void MatrixPackKernel(int n, const int *offsets, const int *columns,
                                       const cuDoubleComplex *a, const double *d, cuComplex *b)
{
  const int row = blockIdx.x * blockDim.x + threadIdx.x;
  if (row < n) for (int j = offsets[row]; j < offsets[row + 1]; ++j)
  {
    const double scale = d[row] * d[columns[j]];
    b[j] = make_cuComplex(float(scale * a[j].x), float(scale * a[j].y));
  }
}

__global__ inline void ResidualKernel(int n, int total, const int *offsets, const int *columns,
                                     const cuDoubleComplex *a, const cuDoubleComplex *x,
                                     const cuDoubleComplex *b, cuDoubleComplex *r)
{
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < total)
  {
    const int row = i % n, first = i - row;
    double re = 0.0, im = 0.0;
    for (int j = offsets[row]; j < offsets[row + 1]; ++j)
    {
      const auto value = a[j], v = x[first + columns[j]];
      re += value.x * v.x - value.y * v.y;
      im += value.x * v.y + value.y * v.x;
    }
    r[i] = make_cuDoubleComplex(b[i].x - re, b[i].y - im);
  }
}

inline bool Valid(int n, int nrhs) { return n >= 0 && nrhs > 0 && 1LL * n * nrhs <= INT_MAX; }
inline int Blocks(int n) { return int((1LL * n + 255) / 256); }

inline cudaError_t Pack(int n, int nrhs, const double *d, const cuDoubleComplex *x,
                       cuComplex *y, cudaStream_t stream = nullptr, int *invalid = nullptr)
{
  if (!Valid(n, nrhs)) return cudaErrorInvalidValue;
  if (n) PackKernel<<<Blocks(n * nrhs), 256, 0, stream>>>(n, n * nrhs, d, x, y, invalid);
  return n ? cudaGetLastError() : cudaSuccess;
}
inline cudaError_t Accumulate(int n, int nrhs, const double *d, const cuComplex *x,
                             cuDoubleComplex *y, bool add, cudaStream_t stream = nullptr)
{
  if (!Valid(n, nrhs)) return cudaErrorInvalidValue;
  if (n) AccumulateKernel<<<Blocks(n * nrhs), 256, 0, stream>>>(n, n * nrhs, d, x, y, add);
  return n ? cudaGetLastError() : cudaSuccess;
}
inline cudaError_t MatrixPack(int n, const int *offsets, const int *columns,
                             const cuDoubleComplex *a, const double *d, cuComplex *b,
                             cudaStream_t stream = nullptr)
{
  if (n < 0) return cudaErrorInvalidValue;
  if (n) MatrixPackKernel<<<Blocks(n), 256, 0, stream>>>(n, offsets, columns, a, d, b);
  return n ? cudaGetLastError() : cudaSuccess;
}
inline cudaError_t Residual(int n, int nrhs, const int *offsets, const int *columns,
                           const cuDoubleComplex *a, const cuDoubleComplex *x,
                           const cuDoubleComplex *b, cuDoubleComplex *r,
                           cudaStream_t stream = nullptr)
{
  if (!Valid(n, nrhs)) return cudaErrorInvalidValue;
  if (n) ResidualKernel<<<Blocks(n * nrhs), 256, 0, stream>>>(n, n * nrhs, offsets, columns, a, x, b, r);
  return n ? cudaGetLastError() : cudaSuccess;
}
}  // namespace palace::mixedcoarse
#endif
