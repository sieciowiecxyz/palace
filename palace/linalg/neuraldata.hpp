// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_LINALG_NEURAL_DATA_HPP
#define PALACE_LINALG_NEURAL_DATA_HPP

#include <span>
#include <vector>

namespace palace
{

class FiniteElementSpace;

struct NeuralProbeFields
{
  // Row-major [true DOF, probe] with eight columns.
  std::vector<double> real, imag;
  double bbox_length;
};

// MFEM projection and bounding-box APIs require a mutable space and mesh.
NeuralProbeFields ProjectNeuralProbeFields(FiniteElementSpace &space,
                                           std::span<const int> essential_tdofs);

}  // namespace palace

#endif  // PALACE_LINALG_NEURAL_DATA_HPP
