// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include <complex>
#include <limits>
#include <memory>
#include <string_view>
#include <catch2/catch_test_macros.hpp>
#include "fem/fespace.hpp"
#include "fem/mesh.hpp"
#include "linalg/complexcsr.hpp"
#include "linalg/hypre.hpp"
#include "linalg/iterative.hpp"
#include "linalg/neuralcoarse.hpp"
#include "linalg/rap.hpp"

namespace palace
{
namespace
{
using namespace std::string_view_literals;

class CoarseTestOperator : public ComplexParOperator
{
public:
  using ComplexParOperator::ComplexParOperator;
  mutable int calls_before_fault = 0;
  mutable int calls = 0;

  void Mult(const ComplexVector &x, ComplexVector &y) const override
  {
    ++calls;
    ComplexParOperator::Mult(x, y);
    if (calls_before_fault > 0 && --calls_before_fault == 0)
    {
      y.Real()[0] += 1.0e6;
    }
  }
};

class CoarseTestFallback : public Solver<ComplexOperator>
{
  const ComplexOperator *&assembled;

public:
  explicit CoarseTestFallback(const ComplexOperator *&assembled) : assembled(assembled) {}
  void SetOperator(const ComplexOperator &op) override { assembled = &op; }

  void Mult(const ComplexVector &rhs, ComplexVector &y) const override
  {
    CHECK(&rhs != &y);
    y = rhs;
  }
};

struct CoarseFixture
{
  mfem::Mesh serial = mfem::Mesh::MakeCartesian3D(1, 1, 1, mfem::Element::TETRAHEDRON);
  Mesh mesh{MPI_COMM_SELF, serial};
  mfem::ND_FECollection nd{1, 3};
  FiniteElementSpace space{mesh, &nd};
  int n = space.GetTrueVSize();
  int constrained = n - 1;
  mfem::Array<int> essential{constrained}, empty;

  std::unique_ptr<hypre::HypreCSRMatrix> Matrix(bool imaginary, double shift)
  {
    auto matrix = std::make_unique<hypre::HypreCSRMatrix>(n, n, n + 2);
    auto *offsets = matrix->GetI();
    auto *columns = matrix->GetJ();
    auto *values = matrix->GetData();
    int pos = 0;
    for (int row = 0; row < n; ++row)
    {
      offsets[row] = pos;
      // HYPRE diagonal extraction expects the diagonal first.
      columns[pos] = row;
      if (row < 2)
      {
        values[pos++] =
            imaginary ? (row == 0 ? 1.0 : -0.5) : (row == 0 ? 4.0 : 3.0) + shift;
        columns[pos] = 1 - row;
        values[pos++] = imaginary ? (row == 0 ? -0.75 : 0.5) : (row == 0 ? 1.0 : -0.25);
      }
      else
      {
        values[pos++] = imaginary ? 0.0 : 1.0;
      }
    }
    offsets[n] = pos;
    return matrix;
  }

  std::unique_ptr<CoarseTestOperator> Operator(bool mask = true, double shift = 0.0)
  {
    auto op = std::make_unique<CoarseTestOperator>(Matrix(false, shift),
                                                   Matrix(true, shift), space);
    op->SetEssentialTrueDofs(mask ? essential : empty, palace::Operator::DIAG_ONE);
    return op;
  }

  void CheckResidual(const ComplexOperator &op, const ComplexVector &rhs,
                     const ComplexVector &y)
  {
    ComplexVector residual(rhs);
    op.AddMult(y, residual, -1.0);
    CHECK(linalg::Norml2(MPI_COMM_SELF, residual) < 1.0e-12);
  }
};
}  // namespace

TEST_CASE("Neural coarse correction solves in a complex rank-revealed subspace",
          "[Serial][NeuralCoarse]")
{
  CoarseFixture f;
  auto op = f.Operator();
  int builds = 0;
  bool rank_zero = false;
  NeuralCoarseSolver solver(MPI_COMM_SELF, {f.n, 2UL * (f.n + 2)},
                            [&](const ComplexParOperator &, const ComplexLocalCSR &csr,
                                std::span<const int> mask, NeuralCoarseSolver::Basis &basis)
                            {
                              ++builds;
                              CHECK(csr.n_loc == f.n);
                              REQUIRE(mask.size() == 1);
                              CHECK(mask.front() == f.constrained);
                              basis.columns = 4;
                              basis.real.assign(4 * f.n, 0.0);
                              basis.imag.assign(4 * f.n, 0.0);
                              if (!rank_zero)
                              {
                                // Columns (1, i), (i, 1), and 2i times column 0 in rows 0
                                // and 1.
                                basis.real[0] = 1.0;
                                basis.imag[1] = 1.0;
                                basis.imag[2] = 2.0;
                                basis.imag[4] = 1.0;
                                basis.real[5] = 1.0;
                                basis.real[6] = -2.0;
                              }
                              basis.imag[4 * f.constrained + 3] = 5.0;
                              return true;
                            },
                            {});
  solver.SetOperator(*op);
  CAPTURE(solver.GetSetupReason());
  REQUIRE(solver.GetRank() == 2);

  ComplexVector exact(f.n), rhs(f.n), y(f.n);
  exact = 0.0;
  exact.Real()[0] = 0.75;
  exact.Imag()[1] = -2.0;
  op->Mult(exact, rhs);
  solver.Mult(rhs, y);
  REQUIRE(solver.GetLastApplyReason() == "corrected"sv);
  f.CheckResidual(*op, rhs, y);
  CHECK(y.Real()[f.constrained] == 0.0);
  CHECK(y.Imag()[f.constrained] == 0.0);

  const std::complex<double> phase(0.6, 0.8);
  rhs *= phase;
  y = rhs;
  solver.Mult(y, y);
  f.CheckResidual(*op, rhs, y);
  exact *= phase;
  y -= exact;
  CHECK(linalg::Norml2(MPI_COMM_SELF, y) < 1.0e-12);

  rhs = 0.0;
  solver.Mult(rhs, y);
  CHECK(linalg::Norml2(MPI_COMM_SELF, y) == 0.0);
  solver.SetInitialGuess(true);
  y = exact;
  solver.Mult(rhs, y);
  f.CheckResidual(*op, rhs, y);
  CHECK(builds == 1);
  solver.SetInitialGuess(false);

  op->Mult(exact, rhs);
  op->calls_before_fault = 2;
  solver.Mult(rhs, y);
  CHECK(solver.GetLastApplyReason() == "correction_rejected"sv);
  CHECK(solver.GetGuardRejections() == 1);

  rank_zero = true;
  solver.SetOperator(*op);
  CHECK(builds == 2);
  CHECK(solver.GetGuardRejections() == 0);
  REQUIRE(solver.GetRank() == 0);
  CHECK(solver.GetSetupReason() == "rank_zero"sv);
  ComplexVector baseline(f.n);
  solver.Mult(rhs, baseline);
  CHECK(solver.GetLastApplyReason() == "jacobi_only"sv);
  y -= baseline;
  CHECK(linalg::Norml2(MPI_COMM_SELF, y) == 0.0);
  op->AddMult(baseline, rhs, -1.0);
  CHECK(linalg::Norml2(MPI_COMM_SELF, rhs) > 0.1);
}

TEST_CASE("Neural coarse rebuilds and defers classical setup until admitted",
          "[Serial][NeuralCoarse]")
{
  CoarseFixture f;
  auto empty = f.Operator(false);
  auto masked = f.Operator(true);
  auto changed = f.Operator(true, 2.0);
  bool invalid = false;
  int builds = 0, factories = 0;
  const ComplexOperator *assembled = nullptr;
  NeuralCoarseSolver solver(
      MPI_COMM_SELF, {f.n, 2UL * (f.n + 2)},
      [&](const ComplexParOperator &op, const ComplexLocalCSR &, std::span<const int> mask,
          NeuralCoarseSolver::Basis &basis)
      {
        ++builds;
        CHECK(mask.size() == (&op == empty.get() ? 0 : 1));
        if (mask.empty())
        {
          return false;
        }
        basis.columns = 1;
        basis.real.assign(f.n, 0.0);
        basis.imag.assign(f.n, 0.0);
        basis.real[0] = invalid ? std::numeric_limits<double>::quiet_NaN() : 1.0;
        return true;
      },
      [&]()
      {
        ++factories;
        return std::make_unique<CoarseTestFallback>(assembled);
      },
      true);

  solver.SetOperator(*empty);
  CHECK(solver.GetSetupReason() == "basis_unavailable"sv);
  CHECK(solver.HasRequestedClassical());
  solver.SetOperator(*masked);
  CAPTURE(solver.GetSetupReason());
  REQUIRE(solver.GetRank() == 1);
  CHECK_FALSE(solver.HasRequestedClassical());

  ComplexVector rhs(f.n), y(f.n);
  rhs = 0.0;
  rhs.Imag()[f.constrained] = 1.0;
  y = rhs;
  solver.SetInitialGuess(true);
  solver.Mult(y, y);
  CHECK(y.Imag()[f.constrained] == 1.0);
  CHECK(solver.GetLastApplyReason() == "inhomogeneous_essential_dofs"sv);
  REQUIRE(solver.HasRequestedClassical());
  solver.SetInitialGuess(false);
  solver.Mult(rhs, y);
  CHECK(linalg::Norml2(MPI_COMM_SELF, y) == 0.0);
  CHECK(factories == 0);
  CHECK(assembled == nullptr);

  solver.UseClassical();
  y = rhs;
  solver.Mult(y, y);
  CHECK(y.Imag()[f.constrained] == 1.0);
  solver.Mult(rhs, y);
  CHECK(assembled == masked.get());
  CHECK(factories == 1);

  invalid = true;
  solver.SetOperator(*changed);
  CHECK(solver.GetSetupReason() == "invalid_basis"sv);
  CHECK(solver.HasRequestedClassical());
  CHECK(builds == 3);
  CHECK(factories == 1);
  solver.UseClassical();
  solver.Mult(rhs, y);
  CHECK(factories == 2);
  CHECK(assembled == changed.get());
}

TEST_CASE("FGMRES continuation admits classical coarse work within the remaining budget",
          "[Serial][NeuralCoarse]")
{
  CoarseFixture f;
  auto op = f.Operator();
  const ComplexOperator *assembled = nullptr;
  NeuralCoarseSolver coarse(
      MPI_COMM_SELF, {f.n, 2UL * (f.n + 2)},
      [&](const ComplexParOperator &, const ComplexLocalCSR &, std::span<const int>,
          NeuralCoarseSolver::Basis &basis)
      {
        basis.columns = 1;
        basis.real.assign(f.n, 0.0);
        basis.imag.assign(f.n, 0.0);
        basis.real[0] = 1.0;
        return true;
      },
      [&]() { return std::make_unique<CoarseTestFallback>(assembled); }, true);
  coarse.SetOperator(*op);
  CAPTURE(coarse.GetSetupReason());
  REQUIRE(coarse.GetRank() == 1);

  FgmresSolver<ComplexOperator> solver(MPI_COMM_SELF, 0);
  solver.SetOperator(*op);
  solver.SetPreconditioner(coarse);
  constexpr int total_iterations = 3;
  constexpr double epsilon = 1.0e-12;
  solver.SetMaxIter(total_iterations);

  ComplexVector rhs(f.n), x(f.n);
  rhs = 0.0;
  rhs.Real()[0] = 1.0;
  rhs.Imag()[1] = 2.0;
  x = 0.0;

  // Reject the first trial correction at its explicit physical residual check.
  op->calls_before_fault = 2;
  std::size_t trial_matvecs = 0;
  solver.MultBounded(
      rhs, x, total_iterations, epsilon, false,
      [&]() { return coarse.GetGuardRejections() > 0; }, &trial_matvecs);
  REQUIRE(coarse.GetGuardRejections() == 1);
  REQUIRE(solver.GetNumIterations() == 1);
  CHECK(trial_matvecs == 1);
  CHECK(linalg::Norml2(MPI_COMM_SELF, x) == 0.0);
  REQUIRE(assembled == nullptr);
  const int remaining = total_iterations - solver.GetNumIterations();

  const int calls = op->calls;
  solver.MultBounded(rhs, x, remaining, epsilon, true, []() { return true; });
  CHECK(solver.GetNumIterations() == 0);
  CHECK(op->calls == calls);
  CHECK(assembled == nullptr);

  coarse.UseClassical();
  CHECK(assembled == nullptr);
  solver.MultBounded(rhs, x, remaining, epsilon, true, []() { return false; });
  CHECK(solver.GetNumIterations() == remaining);
  CHECK(assembled == op.get());
  f.CheckResidual(*op, rhs, x);
}
}  // namespace palace
