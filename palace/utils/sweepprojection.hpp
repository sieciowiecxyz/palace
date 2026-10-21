// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_UTILS_SWEEPPROJECTION_HPP
#define PALACE_UTILS_SWEEPPROJECTION_HPP

#include <cmath>
#include <complex>
#include <optional>

namespace palace
{
// Given u = d / ||d||, form alpha = (u^H r0) / ||d|| without squaring ||d||.
// Bound cancellation in the initial approximation; final selection uses original A(f).
inline std::optional<std::complex<double>> SweepProjectionCoefficient(
    std::complex<double> unit_image_dot_residual, double image_norm)
{
  if (!std::isfinite(image_norm) || image_norm <= 0.0 ||
      !std::isfinite(unit_image_dot_residual.real()) ||
      !std::isfinite(unit_image_dot_residual.imag()))
    return std::nullopt;
  const auto alpha = unit_image_dot_residual / image_norm;
  if (!std::isfinite(alpha.real()) || !std::isfinite(alpha.imag()) ||
      std::abs(alpha) > 1.0e6)
    return std::nullopt;
  return alpha;
}
}  // namespace palace

#endif
