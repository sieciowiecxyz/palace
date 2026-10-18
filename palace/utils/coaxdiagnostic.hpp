// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_UTILS_COAXDIAGNOSTIC_HPP
#define PALACE_UTILS_COAXDIAGNOSTIC_HPP

#include <array>
#include <cmath>
#include <mfem.hpp>
#include "fem/gridfunction.hpp"
#include "utils/communication.hpp"
#include "utils/units.hpp"
#include "utils/timer.hpp"

namespace palace
{

// Diagnostic for the verified coax fixtures ONLY. Not a general analytic
// boundary condition or a correction to a computed field. The local runner verifies
// the mesh/config before enabling it. Integrates the actual FE field error over
// all tetrahedra; compare two quadrature orders to expose integration sensitivity.
inline void CheckCoaxTEM(GridFunction &E, GridFunction &B, const Units &units,
                         double omega, int excitation, double length)
{
  MFEM_VERIFY(excitation == 1 || excitation == 2, "Coax diagnostic needs ports 1/2!");
  MFEM_VERIFY(std::isfinite(length) && length > 0.0, "Invalid coax diagnostic length!");
  constexpr double eps = 2.1, c = 299792458.0;
  constexpr double a = 0.000120, b = 0.00040179519190143026;
  const double voltage = std::sqrt(50.0);
  const double beta = units.Dimensionalize<Units::ValueType::FREQUENCY>(omega) *
                      1.0e9 * std::sqrt(eps) / c;
  const double length_scale = units.GetScaleFactor<Units::ValueType::LENGTH>();
  const double norm_e = std::sqrt(2.0 * M_PI * length * voltage * voltage / std::log(b / a));
  for (int order : {4, 6})
  {
    const auto started = Timer::Now();
    std::array<const mfem::IntegrationRule *, mfem::Geometry::NumGeom> rules{};
    rules[mfem::Geometry::TETRAHEDRON] =
        &mfem::IntRules.Get(mfem::Geometry::TETRAHEDRON, order);
    auto error = [&](GridFunction &field, bool magnetic)
    {
      const double scale = magnetic ? units.GetScaleFactor<Units::ValueType::FIELD_B>() :
                                      units.GetScaleFactor<Units::ValueType::FIELD_E>();
      auto value = [&](const mfem::Vector &point, mfem::Vector &v, bool imaginary)
      {
        const double x = point(0) * length_scale, y = point(1) * length_scale;
        const double z = point(2) * length_scale, r2 = x * x + y * y;
        const double distance = excitation == 1 ? z : length - z;
        const double phase = imaginary ? -std::sin(beta * distance) : std::cos(beta * distance);
        const double common = voltage * phase / (r2 * std::log(b / a) * scale);
        v(0) = common * x;
        v(1) = common * y;
        v(2) = 0.0;
        if (magnetic)
        {
          const double direction = excitation == 1 ? 1.0 : -1.0;
          v(0) = -common * y * direction * std::sqrt(eps) / c;
          v(1) = common * x * direction * std::sqrt(eps) / c;
        }
      };
      mfem::VectorFunctionCoefficient real(3, [&](const mfem::Vector &x, mfem::Vector &v)
                                            { value(x, v, false); });
      mfem::VectorFunctionCoefficient imag(3, [&](const mfem::Vector &x, mfem::Vector &v)
                                            { value(x, v, true); });
      const double er = field.Real().ComputeL2Error(real, rules.data());
      const double ei = field.Imag().ComputeL2Error(imag, rules.data());
      const double norm = magnetic ? norm_e * std::sqrt(eps) / c : norm_e;
      return std::hypot(er, ei) * scale * std::pow(length_scale, 1.5) / norm;
    };
    const double e_error = error(E, false), b_error = error(B, true);
    Mpi::Print(E.GetComm(),
               "PALACE_TEM_L2: quadrature={} excitation={} relative_E={:.12e} relative_B={:.12e} seconds={:.6f}\n",
               order, excitation, e_error, b_error,
               Timer::Duration(Timer::Now() - started).count());
  }
}

}  // namespace palace

#endif
