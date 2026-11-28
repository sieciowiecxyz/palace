// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_LINALG_NEURAL_DATA_HPP
#define PALACE_LINALG_NEURAL_DATA_HPP

#include <cstddef>
#include <filesystem>
#include <memory>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

namespace palace
{

class ComplexParOperator;
class ComplexVector;
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

struct NeuralCaptureMetadata
{
  std::string geometry_id, mesh_sha256, source_sha, config_sha256;
  double omega;
  bool pc_mat_shifted, pc_mat_real;
};

struct NeuralCaptureLimits
{
  int max_rows;
  std::size_t max_nnz, max_bytes, max_samples;
};

// A configured quota can skip a capture without invalidating the solve.
class NeuralCaptureBudgetExceeded : public std::length_error
{
public:
  using std::length_error::length_error;
};

// One snapshot per SetOperator. Capture is opt-in and excluded from timed runs.
class NeuralCapture
{
public:
  NeuralCapture(const ComplexParOperator &bc, FiniteElementSpace &coarse_space,
                const NeuralCaptureMetadata &metadata, const NeuralCaptureLimits &limits);
  ~NeuralCapture();

  // Call with X[0] just before the coarse solve. Returns false at the sample
  // cap.
  bool AppendRhs(const ComplexVector &rhs, int excitation_id);

  // Publish one complete capture to a fresh output path and return its size in bytes.
  std::size_t Write(const std::filesystem::path &path) const;

private:
  struct Data;
  std::unique_ptr<Data> data;
};

}  // namespace palace

#endif  // PALACE_LINALG_NEURAL_DATA_HPP
