// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include "neuralcoarse.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <new>
#include <string_view>
#include <utility>
#include <Eigen/QR>
#include <Eigen/SVD>
#include <mfem/general/backends.hpp>
#include "fem/libceed/operator.hpp"
#include "linalg/complexcsr.hpp"
#include "linalg/hypre.hpp"
#include "linalg/jacobi.hpp"
#include "linalg/rap.hpp"
#include "utils/timer.hpp"

namespace palace
{

namespace
{

constexpr double roundoff = 64.0 * std::numeric_limits<double>::epsilon();
constexpr int max_basis_columns = 16;

bool Homogeneous(const ComplexVector &v, std::span<const int> essential)
{
  if (essential.empty())
  {
    return true;
  }
  const auto *real = v.Real().HostRead();
  const auto *imag = v.Imag().HostRead();
  return std::all_of(essential.begin(), essential.end(),
                     [&](int i) { return real[i] == 0.0 && imag[i] == 0.0; });
}

double Norm(MPI_Comm comm, const ComplexVector &v)
{
  const double norm = linalg::Norml2(comm, v);
  if (norm > 0.0 && std::isfinite(norm))
  {
    return norm;
  }
  // Recover from underflow or overflow of the squared norm. This path is single-rank.
  const auto *real = v.Real().HostRead();
  const auto *imag = v.Imag().HostRead();
  double stable_norm = 0.0;
  for (int i = 0; i < v.Size(); i++)
  {
    if (!std::isfinite(real[i]) || !std::isfinite(imag[i]))
    {
      return std::numeric_limits<double>::quiet_NaN();
    }
    stable_norm = std::hypot(stable_norm, real[i], imag[i]);
  }
  return stable_norm;
}

bool CanAssemble(const Operator *local)
{
  return !local || dynamic_cast<const hypre::HypreCSRMatrix *>(local) ||
         dynamic_cast<const ceed::Operator *>(local);
}

// The sum bounds the merged CSR allocation even when the patterns overlap.
bool WithinNnzLimit(const ComplexParOperator &op, std::size_t remaining)
{
  for (const auto *part : {op.Real(), op.Imag()})
  {
    if (part)
    {
      const auto &assembled = static_cast<const ParOperator &>(*part).ParallelAssemble();
      const auto nnz = static_cast<std::size_t>(assembled.NNZ());
      if (nnz > remaining)
      {
        return false;
      }
      remaining -= nnz;
    }
  }
  return true;
}

bool ValidateDiagonal(const ComplexParOperator &op, const ComplexLocalCSR &csr,
                      std::span<const int> essential, double &frob)
{
  double scale = 0.0;
  std::size_t next_essential = 0;
  for (int i = 0; i < csr.n_loc; i++)
  {
    double row_sum = 0.0;
    for (auto j = csr.I[i]; j < csr.I[i + 1]; j++)
    {
      const double magnitude = std::abs(csr.V[j]);
      if (!std::isfinite(magnitude))
      {
        return false;
      }
      row_sum += magnitude;
      frob = std::hypot(frob, magnitude);
    }
    if (next_essential < essential.size() && essential[next_essential] == i)
    {
      next_essential++;
    }
    else
    {
      scale = std::max(scale, row_sum);
    }
  }
  if (!(scale > 0.0 && std::isfinite(scale) && std::isfinite(frob)))
  {
    return false;
  }

  ComplexVector diagonal(csr.n_loc);
  op.AssembleDiagonal(diagonal);
  const auto *real = diagonal.Real().HostRead();
  const auto *imag = diagonal.Imag().HostRead();
  for (int i = 0; i < csr.n_loc; i++)
  {
    const auto begin = csr.J.begin() + csr.I[i];
    const auto end = csr.J.begin() + csr.I[i + 1];
    const auto entry = std::lower_bound(begin, end, i);
    if (entry == end || *entry != i)
    {
      return false;
    }
    const auto expected = csr.V[entry - csr.J.begin()];
    const std::complex<double> d(real[i], imag[i]);
    const double abs_d = std::abs(d);
    const double square = real[i] * real[i] + imag[i] * imag[i];
    if (!(abs_d > roundoff * scale && std::isfinite(abs_d) &&
          std::abs(d - expected) <= roundoff * std::max(abs_d, std::abs(expected)) &&
          square > 0.0 && std::isfinite(square) && std::isfinite(1.0 / square)))
    {
      return false;
    }
  }
  return true;
}

}  // namespace

struct NeuralCoarseSolver::Correction
{
  JacobiSmoother<ComplexOperator> jacobi;
  std::vector<int> essential;
  std::vector<std::unique_ptr<ComplexVector>> u;
  std::vector<ComplexVector> q;
  Eigen::MatrixXcd r;
  double frob = 0.0;
  ComplexVector r0, z0, baseline, e, update, candidate, residual;

  Correction(MPI_Comm comm, int n)
    : jacobi(comm, 2.0 / 3.0), r0(n), z0(n), baseline(n), e(n), update(n), candidate(n),
      residual(n)
  {
    for (auto *v : {&r0, &z0, &baseline, &e, &update, &candidate, &residual})
    {
      v->UseDevice(true);
    }
  }

  ~Correction()
  {
    if (mfem::Device::Allows(mfem::Backend::CUDA_MASK | mfem::Backend::HIP_MASK))
    {
      MFEM_DEVICE_SYNC;
    }
  }

  const char *BuildQR(const ComplexOperator &op, const Basis &basis)
  {
    const int n = op.Height();
    const int k = basis.columns;
    Eigen::MatrixXcd w(n, k);
    std::vector<std::unique_ptr<ComplexVector>> directions;
    directions.reserve(k);
    ComplexVector direction(n), image(n);
    direction.UseDevice(true);
    image.UseDevice(true);
    for (int j = 0; j < k; j++)
    {
      auto *real = direction.Real().HostWrite();
      auto *imag = direction.Imag().HostWrite();
      for (int i = 0; i < n; i++)
      {
        const auto index = static_cast<std::size_t>(i) * k + j;
        real[i] = basis.real[index];
        imag[i] = basis.imag[index];
        if (!std::isfinite(real[i]) || !std::isfinite(imag[i]))
        {
          return "invalid_basis";
        }
      }
      for (int i : essential)
      {
        real[i] = imag[i] = 0.0;
      }
      op.Mult(direction, image);
      const auto column = static_cast<int>(directions.size());
      image.Get(w.col(column).data(), n, false);
      if (!w.col(column).allFinite())
      {
        return "invalid_qr";
      }
      const double scale = w.col(column).stableNorm();
      if (scale == 0.0 && w.col(column).isZero(0.0))
      {
        continue;
      }
      const double inverse = 1.0 / scale;
      if (!std::isfinite(scale) || !std::isfinite(inverse) || inverse == 0.0)
      {
        return "invalid_qr";
      }
      w.col(column) *= inverse;
      real = direction.Real().HostReadWrite();
      imag = direction.Imag().HostReadWrite();
      // Normalize U on the host alongside W. Check both before committing the columns.
      for (int i = 0; i < n; i++)
      {
        const std::complex<double> raw(real[i], imag[i]);
        const auto normalized = raw * inverse;
        if (!std::isfinite(normalized.real()) || !std::isfinite(normalized.imag()) ||
            (raw != 0.0 && normalized == 0.0))
        {
          return "invalid_qr";
        }
        real[i] = normalized.real();
        imag[i] = normalized.imag();
      }
      directions.push_back(std::make_unique<ComplexVector>(direction));
    }
    if (directions.empty())
    {
      return "rank_zero";
    }

    const auto images = w.leftCols(directions.size());
    const double quality = roundoff * std::sqrt(static_cast<double>(std::max(n, k)));
    const double tau = std::max(1.0e-10, quality);
    const Eigen::ColPivHouseholderQR<Eigen::MatrixXcd> qr(images);
    const auto pivots = qr.colsPermutation().indices();
    int rank = 0;
    while (rank < std::min(images.rows(), images.cols()) &&
           std::abs(qr.matrixR()(rank, rank)) > tau)
    {
      rank++;
    }

    Eigen::MatrixXcd triangular;
    for (; rank > 0; rank--)
    {
      triangular = qr.matrixR().topLeftCorner(rank, rank).triangularView<Eigen::Upper>();
      const Eigen::JacobiSVD<Eigen::MatrixXcd> svd(triangular);
      const auto &singular = svd.singularValues();
      if (svd.info() == Eigen::Success && singular(rank - 1) >= tau * singular(0))
      {
        break;
      }
    }
    if (rank == 0)
    {
      return "rank_zero";
    }
    const Eigen::MatrixXcd thin_q = qr.householderQ() * Eigen::MatrixXcd::Identity(n, rank);
    const double orthogonality =
        (thin_q.adjoint() * thin_q - Eigen::MatrixXcd::Identity(rank, rank)).norm();
    double error = 0.0, norm = 0.0;
    for (int j = 0; j < rank; j++)
    {
      error =
          std::hypot(error, (images.col(pivots(j)) - thin_q * triangular.col(j)).norm());
      norm = std::hypot(norm, images.col(pivots(j)).norm());
    }
    if (!(error <= quality * norm && orthogonality <= quality))
    {
      return "invalid_qr";
    }
    r = std::move(triangular);
    for (int j = 0; j < rank; j++)
    {
      u.push_back(std::move(directions[pivots(j)]));
      q.emplace_back(thin_q.col(j).data(), n, false);
      q.back().UseDevice(true);
    }
    return "ready";
  }
};

NeuralCoarseSolver::NeuralCoarseSolver(MPI_Comm comm, Limits limits,
                                       BasisBuilder build_basis,
                                       ClassicalFactory make_classical,
                                       bool defer_classical)
  : comm(comm), limits(limits), build_basis(std::move(build_basis)),
    make_classical(std::move(make_classical)), defer_classical(defer_classical),
    classical_allowed(!defer_classical)
{
}

NeuralCoarseSolver::~NeuralCoarseSolver() = default;

void NeuralCoarseSolver::SetOperator(const ComplexOperator &next)
{
  correction.reset();
  classical.reset();
  classical_allowed = !defer_classical;
  op = &next;
  height = next.Height();
  width = next.Width();
  apply_reason = "not_applied";
  guard_rejections = 0;
  num_applications = 0;
  classical_setup_seconds = 0.0;
  const auto *par = dynamic_cast<const ComplexParOperator *>(op);
  setup_reason = "unsupported_operator";
  if (Mpi::Size(comm) != 1 || !par || Mpi::Size(par->GetComm()) != 1 || !build_basis ||
      height <= 0 || height != width || par->TrialFiniteElementSpace().IsBroken() ||
      !par->TrialFiniteElementSpace().GetParMesh().Conforming() ||
      par->TrialFiniteElementSpace().GetMaxElementOrder() != 1 ||
      !dynamic_cast<const mfem::ND_FECollection *>(
          &par->TrialFiniteElementSpace().GetFEColl()) ||
      &par->TrialFiniteElementSpace() != &par->TestFiniteElementSpace())
  {
    return;
  }
  const auto &local = par->LocalOperator();
  if ((!local.Real() && !local.Imag()) || !CanAssemble(local.Real()) ||
      !CanAssemble(local.Imag()))
  {
    return;
  }
  setup_reason = "coarse_size_limit";
  if (height > limits.max_rows)
  {
    return;
  }

  try
  {
    std::vector<int> essential;
    if (const auto *dofs = par->GetEssentialTrueDofs())
    {
      const int *ids = dofs->HostRead();
      essential.assign(ids, ids + dofs->Size());
      std::sort(essential.begin(), essential.end());
      if (essential.front() < 0 || essential.back() >= height ||
          std::adjacent_find(essential.begin(), essential.end()) != essential.end())
      {
        setup_reason = "invalid_essential_dofs";
        return;
      }
    }
    if (!WithinNnzLimit(*par, limits.max_nnz))
    {
      return;
    }
    const ComplexLocalCSR csr(next, false);
    if (csr.n_glob != height || csr.n_loc != height || csr.first_row != 0)
    {
      setup_reason = "unsupported_operator";
      return;
    }
    auto state = std::make_unique<Correction>(comm, height);
    state->essential = std::move(essential);
    if (!ValidateDiagonal(*par, csr, state->essential, state->frob))
    {
      setup_reason = "invalid_jacobi_diagonal";
      return;
    }
    Basis basis;
    if (!build_basis(*par, csr, state->essential, basis))
    {
      setup_reason = "basis_unavailable";
      return;
    }
    if (basis.columns < 0 || basis.columns > max_basis_columns ||
        basis.real.size() != static_cast<std::size_t>(height) * basis.columns ||
        basis.imag.size() != basis.real.size())
    {
      setup_reason = "invalid_basis";
      return;
    }
    state->jacobi.SetOperator(next);
    setup_reason = state->BuildQR(next, basis);
    const std::string_view status(setup_reason);
    if (status == "ready" || status == "rank_zero")
    {
      correction = std::move(state);
    }
  }
  catch (const std::bad_alloc &)
  {
    setup_reason = "coarse_allocation_failed";
  }
}

void NeuralCoarseSolver::UseClassical()
{
  correction.reset();
  classical_allowed = true;
  apply_reason = "classical";
}

int NeuralCoarseSolver::GetRank() const
{
  return correction ? static_cast<int>(correction->q.size()) : 0;
}

void NeuralCoarseSolver::ApplyClassical(const ComplexVector &rhs, ComplexVector &y) const
{
  if (!classical_allowed)
  {
    if (!initial_guess)
    {
      y = 0.0;
    }
    return;
  }
  if (!classical)
  {
    MFEM_VERIFY(make_classical, "Neural coarse solver requires a classical fallback!");
    const auto start = Timer::Now();
    auto solver = make_classical();
    MFEM_VERIFY(solver, "Neural coarse classical factory returned no solver!");
    solver->SetOperator(*op);
    classical_setup_seconds = Timer::Duration(Timer::Now() - start).count();
    classical = std::move(solver);
  }
  classical->SetInitialGuess(initial_guess);
  // Stage the input before handing off to a solver whose aliased-input support is unknown.
  const ComplexVector copy(rhs);
  classical->Mult(copy, y);
}

void NeuralCoarseSolver::Mult(const ComplexVector &rhs, ComplexVector &y) const
{
  MFEM_VERIFY(op && rhs.Size() == height && y.Size() == width,
              "Neural coarse solver requires a compatible operator and vectors!");
  num_applications++;
  if (!correction)
  {
    if (apply_reason == std::string_view("not_applied"))
    {
      apply_reason = "classical";
    }
    ApplyClassical(rhs, y);
    return;
  }

  auto &c = *correction;
  if (!Homogeneous(rhs, c.essential) || (initial_guess && !Homogeneous(y, c.essential)))
  {
    apply_reason = "inhomogeneous_essential_dofs";
    correction.reset();
    ApplyClassical(rhs, y);
    return;
  }

  c.r0 = rhs;
  if (initial_guess)
  {
    op->AddMult(y, c.r0, -1.0);
  }
  c.jacobi.Mult(c.r0, c.z0);
  c.baseline = c.z0;
  if (initial_guess)
  {
    c.baseline += y;
  }
  op->Mult(c.baseline, c.residual);
  linalg::AXPBY(1.0, rhs, -1.0, c.residual);
  const double baseline_norm = Norm(comm, c.residual);
  if (!std::isfinite(baseline_norm))
  {
    apply_reason = "nonfinite_jacobi_residual";
    correction.reset();
    ApplyClassical(rhs, y);
    return;
  }

  if (c.q.empty())
  {
    apply_reason = "jacobi_only";
    y = c.baseline;
    return;
  }

  if (initial_guess)
  {
    op->Mult(c.z0, c.e);
    linalg::AXPBY(1.0, c.r0, -1.0, c.e);
  }
  const auto &e = initial_guess ? c.e : c.residual;
  const int rank = GetRank();
  Eigen::Matrix<std::complex<double>, Eigen::Dynamic, 1, 0, max_basis_columns> coeff(rank);
  for (int j = 0; j < rank; j++)
  {
    coeff(j) = linalg::Dot(comm, e, c.q[j]);
  }
  c.r.triangularView<Eigen::Upper>().solveInPlace(coeff);
  if (coeff.allFinite())
  {
    c.update = 0.0;
    for (int j = 0; j < rank; j++)
    {
      c.update.AXPY(coeff(j), *c.u[j]);
    }
    c.candidate = c.baseline;
    c.candidate += c.update;
    op->Mult(c.candidate, c.residual);
    linalg::AXPBY(1.0, rhs, -1.0, c.residual);
    const double actual = Norm(comm, c.residual);
    const double r0_norm = Norm(comm, c.r0);
    const double z0_norm = Norm(comm, c.z0);
    const double update_norm = Norm(comm, c.update);
    const double slack = std::min(roundoff * std::sqrt(static_cast<double>(height)) *
                                      (r0_norm + c.frob * (z0_norm + update_norm)),
                                  1.0e-10 * std::max(r0_norm, baseline_norm));
    if (std::isfinite(actual) && std::isfinite(r0_norm) && std::isfinite(z0_norm) &&
        std::isfinite(update_norm) && std::isfinite(slack) &&
        actual - baseline_norm <= slack)
    {
      apply_reason = "corrected";
      y = c.candidate;
      return;
    }
  }
  guard_rejections++;
  apply_reason = "correction_rejected";
  y = c.baseline;
}

}  // namespace palace
