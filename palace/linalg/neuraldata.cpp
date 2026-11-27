// SPDX-License-Identifier: Apache-2.0

#include "neuraldata.hpp"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <stdexcept>
#include <mfem.hpp>
#include "fem/fespace.hpp"
#include "utils/communication.hpp"

namespace palace
{

NeuralProbeFields ProjectNeuralProbeFields(FiniteElementSpace &space,
                                           std::span<const int> essential_tdofs)
{
  constexpr int width = 8;
  const int n = space.GetTrueVSize();
  if (Mpi::Size(space.GetComm()) != 1 || space.IsBroken() ||
      !space.GetParMesh().Conforming() || space.SpaceDimension() != 3 ||
      space.GetMaxElementOrder() != 1 ||
      !dynamic_cast<const mfem::ND_FECollection *>(&space.GetFEColl()) || n <= 0 ||
      n != space.GlobalTrueVSize() ||
      std::any_of(essential_tdofs.begin(), essential_tdofs.end(),
                  [=](int i) { return i < 0 || i >= n; }))
  {
    throw std::invalid_argument(
        "Neural probes require conforming single-rank ND1 true DOFs");
  }

  mfem::Vector lo, hi;
  space.GetParMesh().GetBoundingBox(lo, hi);
  mfem::Vector center(hi);
  center += lo;
  center *= 0.5;
  hi -= lo;
  const double length = hi.Max();
  if (!std::isfinite(length) || length <= 0.0)
  {
    throw std::invalid_argument(
        "Neural probes require a finite positive bounding-box extent");
  }

  const auto size = static_cast<std::size_t>(n) * width;
  NeuralProbeFields result{std::vector<double>(size), std::vector<double>(size), length};
  mfem::ParGridFunction projected(&space.Get());
  mfem::Vector true_dofs(n);
  for (int j = 0; j < width; ++j)
  {
    mfem::VectorFunctionCoefficient field(3,
                                          [&, j](const mfem::Vector &x, mfem::Vector &y)
                                          {
                                            const double a = (x[0] - center[0]) / length;
                                            const double b = (x[1] - center[1]) / length;
                                            const double c = (x[2] - center[2]) / length;
                                            y = 0.0;
                                            switch (j)
                                            {
                                              case 0:
                                                y[0] = 1.0;
                                                break;
                                              case 1:
                                                y[1] = 1.0;
                                                break;
                                              case 2:
                                                y[2] = 1.0;
                                                break;
                                              case 3:
                                                y[1] = a;
                                                break;
                                              case 4:
                                                y[2] = b;
                                                break;
                                              case 5:
                                                y[0] = c;
                                                break;
                                              case 6:
                                                y[2] = std::sin(std::numbers::pi * a);
                                                break;
                                              case 7:
                                                y[0] = std::sin(std::numbers::pi * b);
                                                break;
                                            }
                                            y /= length;
                                          });
    projected.ProjectCoefficient(field);
    projected.GetTrueDofs(true_dofs);
    auto *values = true_dofs.HostReadWrite();
    for (int i : essential_tdofs)
    {
      values[i] = 0.0;
    }

    for (int i = 0; i < n; ++i)
    {
      result.real[static_cast<std::size_t>(i) * width + j] = values[i];
    }
  }
  return result;
}

}  // namespace palace
