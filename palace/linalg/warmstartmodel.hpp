// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_LINALG_WARMSTARTMODEL_HPP
#define PALACE_LINALG_WARMSTARTMODEL_HPP

#include <array>
#include <filesystem>
#include <string>
#include <vector>

namespace palace
{

class ComplexVector;

// CPU inference for a real POD basis in one single-rank finite-element space.
class WarmStartModel
{
public:
  // Throws std::exception on invalid or incompatible bundles.
  WarmStartModel(const std::filesystem::path &path, const std::string &space_id, int n);

  // Resizes and fills candidate on success. Rejected predictions leave it
  // untouched.
  bool Predict(double omega, int excitation, double rhs_norm,
               ComplexVector &candidate) const;

private:
  static constexpr int feature_count = 3;
  static constexpr int hidden_width = 128;

  struct Layer
  {
    std::vector<double> weight, bias;  // Weight rows are contiguous.
  };

  int n, rank;
  std::vector<int> excitations;
  std::array<double, feature_count> mean, scale;
  std::vector<double> basis;  // One contiguous row per degree of freedom.
  std::array<Layer, 5> layers;
};

}  // namespace palace

#endif  // PALACE_LINALG_WARMSTARTMODEL_HPP
