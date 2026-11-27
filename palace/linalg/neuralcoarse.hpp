// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_LINALG_NEURAL_COARSE_HPP
#define PALACE_LINALG_NEURAL_COARSE_HPP

#include <cstddef>
#include <functional>
#include <memory>
#include <span>
#include <vector>
#include "linalg/solver.hpp"

namespace palace
{

class ComplexParOperator;
struct ComplexLocalCSR;

// The caller admits the scope and backend memory budget, and owns the outer solve budget.
class NeuralCoarseSolver final : public Solver<ComplexOperator>
{
public:
  struct Limits
  {
    int max_rows;
    std::size_t max_nnz;
  };

  struct Basis
  {
    int columns = 0;
    std::vector<double> real, imag;  // Split row-major in coarse true-DOF order.
  };

  using BasisBuilder =
      std::function<bool(const ComplexParOperator &, const ComplexLocalCSR &,
                         std::span<const int> essential_tdofs, Basis &)>;
  using ClassicalFactory = std::function<std::unique_ptr<Solver<ComplexOperator>>()>;

  NeuralCoarseSolver(MPI_Comm comm, Limits limits, BasisBuilder build_basis,
                     ClassicalFactory make_classical, bool defer_classical = false);
  ~NeuralCoarseSolver() override;

  void SetOperator(const ComplexOperator &op) override;
  void Mult(const ComplexVector &rhs, ComplexVector &y) const override;

  // Release correction state immediately. Classical setup is deferred until Mult().
  void UseClassical();
  // The outer solve can defer the first classical setup until it admits a continuation.
  bool HasCorrection() const { return static_cast<bool>(correction); }
  bool HasRequestedClassical() const { return op && !correction && !classical_allowed; }
  int GetRank() const;
  std::size_t GetNumApplications() const { return num_applications; }
  double GetClassicalSetupSeconds() const { return classical_setup_seconds; }
  const char *GetSetupReason() const { return setup_reason; }
  const char *GetLastApplyReason() const { return apply_reason; }
  std::size_t GetGuardRejections() const { return guard_rejections; }

private:
  struct Correction;
  void ApplyClassical(const ComplexVector &rhs, ComplexVector &y) const;

  MPI_Comm comm;
  Limits limits;
  BasisBuilder build_basis;
  ClassicalFactory make_classical;
  bool defer_classical, classical_allowed;
  const ComplexOperator *op = nullptr;
  mutable std::unique_ptr<Correction> correction;
  mutable std::unique_ptr<Solver<ComplexOperator>> classical;
  const char *setup_reason = "operator_unset";
  mutable const char *apply_reason = "not_applied";
  mutable std::size_t guard_rejections = 0, num_applications = 0;
  mutable double classical_setup_seconds = 0.0;
};

}  // namespace palace

#endif  // PALACE_LINALG_NEURAL_COARSE_HPP
