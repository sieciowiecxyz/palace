// SPDX-License-Identifier: Apache-2.0
// Small nonsymmetric complex systems, independent long-double coefficient oracle.
#include "palace/utils/sweepprojection.hpp"
#include <array>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>

using C = std::complex<double>;
using L = std::complex<long double>;
using V = std::array<C, 8>;
using M = std::array<V, 8>;
V Apply(const M &a, const V &x)
{
  V y{};
  for (int i = 0; i < 8; ++i)
    for (int j = 0; j < 8; ++j) y[i] += a[i][j] * x[j];
  return y;
}
double Norm(const V &x)
{
  double n = 0.0;
  for (auto v : x) n = std::hypot(n, std::abs(v));
  return n;
}
void Require(bool ok)
{
  if (!ok) throw std::runtime_error("projection oracle failed");
}
int main()
{
  std::mt19937_64 gen(20261021);
  std::uniform_real_distribution<double> random(-1.0, 1.0);
  int count = 0, wrong_dot_detected = 0, stale_image_detected = 0;
  double max_error = 0.0, max_orthogonality = 0.0;
  for (double scale : {1.0e-120, 1.0, 1.0e120})
    for (int case_i = 0; case_i < 32; ++case_i)
    {
      M a{};
      V previous{}, older{}, direction{}, noise{};
      for (int i = 0; i < 8; ++i)
      {
        previous[i] = C(random(gen), random(gen));
        older[i] = C(random(gen), random(gen));
        direction[i] = previous[i] - older[i];
        noise[i] = C(random(gen), random(gen));
        for (int j = 0; j < 8; ++j)
          a[i][j] = scale * C(random(gen) + (i == j ? 3 : 0), random(gen));
      }
      const V d = Apply(a, direction), ax = Apply(a, previous);
      const double norm = Norm(d);
      C noise_dot{};
      for (int i = 0; i < 8; ++i) noise_dot += std::conj(d[i] / norm) * noise[i];
      V b{}, r0{};
      for (int i = 0; i < 8; ++i)
      {
        noise[i] -= (d[i] / norm) * noise_dot;
        b[i] = ax[i] + C(1.2, 0.7) * d[i] + (0.03 * scale) * noise[i];
        r0[i] = b[i] - ax[i];
      }
      C dot{};
      L cross{}, denominator{};
      for (int i = 0; i < 8; ++i)
      {
        dot += std::conj(d[i] / norm) * r0[i];
        cross += std::conj(L(d[i].real(), d[i].imag())) * L(r0[i].real(), r0[i].imag());
        denominator += std::conj(L(d[i].real(), d[i].imag())) * L(d[i].real(), d[i].imag());
      }
      auto alpha = palace::SweepProjectionCoefficient(dot, norm);
      Require(alpha.has_value());
      const L reference = cross / denominator;
      max_error = std::max(max_error, std::abs(*alpha - C(reference.real(), reference.imag())));
      V trial{}, wrong{}, stale{};
      auto bad_alpha = palace::SweepProjectionCoefficient(std::conj(dot), norm);
      Require(bad_alpha.has_value());
      const C phase = std::polar(1.0, 0.6);
      auto stale_alpha = palace::SweepProjectionCoefficient(std::conj(phase) * dot, norm);
      Require(stale_alpha.has_value());
      for (int i = 0; i < 8; ++i)
      {
        trial[i] = previous[i] + *alpha * direction[i];
        wrong[i] = previous[i] + *bad_alpha * direction[i];
        stale[i] = previous[i] + *stale_alpha * direction[i];
      }
      trial = Apply(a, trial); wrong = Apply(a, wrong); stale = Apply(a, stale);
      C orthogonality{};
      for (int i = 0; i < 8; ++i)
      {
        trial[i] = b[i] - trial[i]; wrong[i] = b[i] - wrong[i]; stale[i] = b[i] - stale[i];
        orthogonality += std::conj(d[i] / norm) * trial[i];
      }
      Require(Norm(trial) <= Norm(r0) * (1 + 1.0e-12));
      Require(Norm(wrong) > 1.1 * Norm(trial)); ++wrong_dot_detected;
      Require(Norm(stale) > 1.1 * Norm(trial)); ++stale_image_detected;
      max_orthogonality = std::max(max_orthogonality, std::abs(orthogonality) / Norm(r0));
      ++count;
    }
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const double inf = std::numeric_limits<double>::infinity();
  for (double n : {0.0, -1.0, nan, inf}) Require(!palace::SweepProjectionCoefficient(C(1), n));
  Require(!palace::SweepProjectionCoefficient(C(nan, 1), 1));
  Require(!palace::SweepProjectionCoefficient(C(1, inf), 1));
  Require(!palace::SweepProjectionCoefficient(C(2.0e6), 1));
  Require(!palace::SweepProjectionCoefficient(C(1.0e300), 1.0e-300));
  Require(palace::SweepProjectionCoefficient(C(1.0e-300, -1.0e-300), 1.0e-300).has_value());
  Require(palace::SweepProjectionCoefficient(C(1.0e300, -1.0e300), 1.0e300).has_value());
  Require(max_error < 1.0e-12 && max_orthogonality < 1.0e-12);
  std::cout << "{\"passed\":true,\"cases\":" << count
            << ",\"wrong_conjugation_detected\":" << wrong_dot_detected
            << ",\"stale_image_detected\":" << stale_image_detected
            << ",\"max_alpha_error\":" << max_error
            << ",\"max_scaled_orthogonality\":" << max_orthogonality << "}\n";
}
