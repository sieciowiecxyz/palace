// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_LINALG_NEURAL_MODEL_HPP
#define PALACE_LINALG_NEURAL_MODEL_HPP

#include <array>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <span>
#include <stdexcept>
#include <vector>

namespace palace
{

// Inference for the v1 single-rank, conforming ND1 model. The caller verifies
// problem scope and provides Phi and context in the matching coarse true-DOF order.
class NeuralModel
{
public:
  // Failed to establish a safe CUDA handoff. This must propagate past the fallback.
  class CudaHandoffError : public std::runtime_error
  {
  public:
    using std::runtime_error::runtime_error;
  };

  static constexpr int PhiColumns = 8;
  static constexpr int BasisColumns = 8;

  enum class Backend
  {
    Cpu,
    Cuda
  };

  struct Device
  {
    Backend backend;
    int index;  // CPU uses 0, CUDA uses the caller-selected ordinal.
  };

  // The caller leaves headroom for backend workspace and allocator reserves, and
  // caps CUDA work using the currently available device memory.
  struct Limits
  {
    std::size_t max_rows, max_nnz, max_working_bytes;
    void Check(std::size_t rows, std::size_t nnz) const;
  };

  struct Input
  {
    std::span<const std::int64_t> indptr, indices;
    std::span<const std::complex<double>> values;
    std::span<const int> essential_tdofs;
    std::span<const double> phi_real, phi_imag;  // Row-major, zero at essential rows.
    std::array<double, 3> context;               // omega*L/c0, shifted flag, real flag.
  };

  struct Basis
  {
    std::vector<double> real, imag;  // Row-major with BasisColumns columns.
  };

  // Reads manifest.json and weights.bin. Throws on a malformed or unsupported bundle.
  explicit NeuralModel(const std::filesystem::path &directory);
  ~NeuralModel();

  NeuralModel(const NeuralModel &) = delete;
  NeuralModel &operator=(const NeuralModel &) = delete;

  // CUDA inference requires exclusive ATen use in this process during the call.
  // Synchronous. All spans must refer to host-valid buffers. Retains no input pointers.
  // Throws on invalid input, budget rejection or inference failure, so that the caller can
  // select the classical fallback.
  Basis Infer(const Input &input, const Limits &limits, Device device) const;

private:
  struct Impl;
  std::unique_ptr<Impl> impl;
};

}  // namespace palace

#endif  // PALACE_LINALG_NEURAL_MODEL_HPP
