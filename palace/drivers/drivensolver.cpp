// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include "drivensolver.hpp"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <iostream>
#include <iterator>
#include <limits>
#include <numbers>
#include <optional>
#include <string>
#include <string_view>
#include <Eigen/Dense>
#include <fmt/core.h>
#include <mfem.hpp>
#include "drivers/fluxerrorestimator.hpp"
#include "fem/errorindicator.hpp"
#include "fem/mesh.hpp"
#include "linalg/errorestimator.hpp"
#include "linalg/floquetcorrection.hpp"
#include "linalg/initialguess.hpp"
#include "linalg/ksp.hpp"
#if defined(PALACE_WITH_ML)
#include "linalg/complexcsr.hpp"
#include "linalg/neuraldata.hpp"
#include "linalg/neuralmodel.hpp"
#include "linalg/rap.hpp"
#endif
#include "linalg/operator.hpp"
#include "linalg/vector.hpp"
#include "models/floquetportoperator.hpp"
#include "models/lumpedportoperator.hpp"
#include "models/portexcitations.hpp"
#include "models/postoperator.hpp"
#include "models/romoperator.hpp"
#include "models/spaceoperator.hpp"
#include "models/surfacecurrentoperator.hpp"
#include "models/waveportoperator.hpp"
#include "utils/communication.hpp"
#include "utils/iodata.hpp"
#include "utils/prettyprint.hpp"
#include "utils/timer.hpp"

namespace palace
{

using namespace std::complex_literals;

namespace
{

double PhysicalNorm(MPI_Comm comm, const ComplexVector &vector)
{
  // Keep the device reduction for ordinary solves. Fall back to scaling when squaring
  // entries can underflow at the scale of the answer or when the reduction overflows.
  const double norm = linalg::Norml2(comm, vector);
  if (std::isfinite(norm) && norm >= 0x1p-480)
  {
    return norm;
  }

  const auto *real = vector.Real().HostRead();
  const auto *imag = vector.Imag().HostRead();
  const int n = vector.Size();
  double scale = 0.0;
  for (int i = 0; i < n; i++)
  {
    if (!std::isfinite(real[i]) || !std::isfinite(imag[i]))
    {
      scale = std::numeric_limits<double>::infinity();
      break;
    }
    scale = std::max({scale, std::abs(real[i]), std::abs(imag[i])});
  }
  Mpi::GlobalMax(1, &scale, comm);
  if (scale == 0.0 || !std::isfinite(scale))
  {
    return scale;
  }
  auto [sum] = linalg::HostSums<1>(0, n,
                                   [&](int i)
                                   {
                                     const double re = real[i] / scale,
                                                  im = imag[i] / scale;
                                     return std::array{re * re + im * im};
                                   });
  Mpi::GlobalSum(1, &sum, comm);
  return scale * std::sqrt(sum);
}

double PhysicalResidual(MPI_Comm comm, const ComplexOperator &A, const ComplexVector &rhs,
                        const ComplexVector &solution)
{
  ComplexVector residual(rhs.Size());
  residual.UseDevice(true);
  A.Mult(solution, residual);
  residual.Add(-1.0, rhs);
  return PhysicalNorm(comm, residual);
}

bool ResidualPasses(double norm, double rhs_norm, double epsilon)
{
  return std::isfinite(rhs_norm) && std::isfinite(epsilon) && std::isfinite(norm) &&
         norm <= epsilon;
}

#if defined(PALACE_WITH_ML)
bool BuildNeuralBasis(FiniteElementSpace &space, const config::LinearSolverData &linear,
                      const ComplexLocalCSR &csr, std::span<const int> essential,
                      double omega, const std::function<bool()> &expired,
                      std::unique_ptr<NeuralModel> &model, NeuralCoarseSolver::Basis &basis)
{
  const auto &settings = linear.neural_coarse;
  if (expired())
  {
    return false;
  }
  if (settings.mode == "S")
  {
    return true;
  }
  auto phi = ProjectNeuralProbeFields(space, essential);
  if (expired())
  {
    return false;
  }
  if (settings.mode == "Phi")
  {
    basis = {NeuralModel::PhiColumns, std::move(phi.real), std::move(phi.imag)};
    return true;
  }

  auto device = NeuralModel::Device{NeuralModel::Backend::Cpu, 0};
  auto working_bytes = settings.max_working_bytes;
#if defined(MFEM_USE_CUDA)
  if (mfem::Device::Allows(mfem::Backend::CUDA_MASK))
  {
    std::size_t free_bytes, total_bytes;
    if (cudaMemGetInfo(&free_bytes, &total_bytes) != cudaSuccess)
    {
      Mpi::Warning("Neural coarse setup could not query available CUDA memory!\n");
      return false;
    }
    working_bytes = std::min(working_bytes, free_bytes);
    device = {NeuralModel::Backend::Cuda, mfem::Device::GetId()};
  }
#endif
  if (!model)
  {
    model = std::make_unique<NeuralModel>(
        std::filesystem::path(settings.model_manifest).parent_path());
  }
  if (expired())
  {
    return false;
  }
  const std::vector<std::int64_t> row(csr.I.begin(), csr.I.end()),
      col(csr.J.begin(), csr.J.end());
  auto learned = model->Infer(
      {row,
       col,
       csr.V,
       essential,
       phi.real,
       phi.imag,
       {omega * phi.bbox_length, double(linear.pc_mat_shifted),
        double(linear.pc_mat_real)}},
      {static_cast<std::size_t>(settings.max_rows), settings.max_nnz, working_bytes},
      device);
  basis = {NeuralModel::BasisColumns, std::move(learned.real), std::move(learned.imag)};
  return !expired();
}

struct CaptureOptions
{
  std::filesystem::path directory;
  NeuralCaptureMetadata metadata;
  NeuralCaptureLimits limits;
  std::size_t bytes_remaining;
  int excitation;
};

CaptureOptions ConfigureNeuralCapture(const char *directory, const IoData &iodata,
                                      const PortExcitations &ports, std::size_t first_solve)
{
  const std::filesystem::path requested(directory);
  MFEM_VERIFY(
      requested.is_relative() &&
          std::ranges::none_of(requested, [](const auto &part) { return part == ".."; }),
      "PALACE_NEURAL_CAPTURE_DIR must be a relative directory within Problem/Output!");
  const auto output =
      std::filesystem::weakly_canonical(std::filesystem::absolute(iodata.problem.output));
  const auto path = std::filesystem::weakly_canonical(std::filesystem::absolute(requested));
  const auto relative = path.lexically_relative(output);
  MFEM_VERIFY(!relative.empty() && relative != "." && *relative.begin() != "..",
              "PALACE_NEURAL_CAPTURE_DIR must be a subdirectory of Problem/Output!");

  MFEM_VERIFY(!ports.Empty(), "Neural capture requires a driven excitation!");
  int excitation = ports.begin()->first;
  if (const char *value = std::getenv("PALACE_NEURAL_CAPTURE_EXCITATION"))
  {
    const std::string_view raw(value);
    const auto [ptr, err] = std::from_chars(raw.begin(), raw.end(), excitation);
    MFEM_VERIFY(err == std::errc{} && ptr == raw.end() && excitation >= 0,
                "Invalid PALACE_NEURAL_CAPTURE_EXCITATION: " << raw);
  }
  const auto entry = ports.excitations.find(excitation);
  MFEM_VERIFY(entry != ports.end() &&
                  static_cast<std::size_t>(std::distance(ports.begin(), entry)) + 1 >=
                      first_solve,
              "Requested neural capture excitation " << excitation
                                                     << " is absent from this sweep!");
  auto require_env = [](const char *name)
  {
    const char *value = std::getenv(name);
    MFEM_VERIFY(value && *value, "Neural capture requires " << name << "!");
    return std::string(value);
  };
  const auto &linear = iodata.solver.linear;
  NeuralCaptureMetadata metadata{require_env("PALACE_NEURAL_GEOMETRY_ID"),
                                 require_env("PALACE_NEURAL_MESH_SHA256"),
                                 require_env("PALACE_NEURAL_SOURCE_SHA"),
                                 require_env("PALACE_NEURAL_CONFIG_SHA256"),
                                 0.0,
                                 bool(linear.pc_mat_shifted),
                                 linear.pc_mat_real};
  std::filesystem::create_directories(path);
  return {
      path,
      std::move(metadata),
      {linear.neural_coarse.max_rows, linear.neural_coarse.max_nnz, 64 * 1024 * 1024, 8},
      256 * 1024 * 1024,
      excitation};
}
#endif

}  // namespace

std::pair<ErrorIndicator, long long int>
DrivenSolver::Solve(const std::vector<std::unique_ptr<Mesh>> &mesh) const
{
  // Set up the spatial discretization and frequency sweep.
  BlockTimer bt0(Timer::CONSTRUCT);
  SpaceOperator space_op(iodata, mesh);
  const auto &port_excitations = space_op.GetPortExcitations();
  SaveMetadata(port_excitations);

  const auto &omega_sample = iodata.solver.driven.sample_f;

  bool adaptive = (iodata.solver.driven.adaptive_tol > 0.0);
  if (adaptive && omega_sample.size() <= iodata.solver.driven.prom_indices.size() &&
      !iodata.solver.driven.adaptive_circuit_synthesis)
  {
    Mpi::Warning("Adaptive frequency sweep requires > {} total frequency samples!\n"
                 "Reverting to uniform sweep!\n",
                 iodata.solver.driven.prom_indices.size());
    adaptive = false;
  }
  SaveMetadata(space_op.GetNDSpaces());
  Mpi::Print("\nComputing {}frequency response for:\n{}", adaptive ? "adaptive fast " : "",
             port_excitations.FmtLog());

  std::size_t restart = iodata.solver.driven.restart;
  if (restart != 1)
  {
    std::size_t max_iter = omega_sample.size() * space_op.GetPortExcitations().Size();
    MFEM_VERIFY(
        restart - 1 < max_iter,
        fmt::format("\"Restart\" ({}) is greater than the number of total samples ({})!",
                    restart, max_iter));

    Mpi::Print("\nRestarting from solve {}", iodata.solver.driven.restart);
  }

  // Main frequency sweep loop.
  if (const char *capture_dir = std::getenv("PALACE_NEURAL_CAPTURE_DIR");
      capture_dir && *capture_dir)
  {
    MFEM_VERIFY(!adaptive, "Neural capture requires a uniform sweep!");
  }
  if (adaptive && (iodata.solver.linear.neural_coarse.Enabled() ||
                   iodata.solver.linear.max_solve_seconds > 0.0))
  {
    Mpi::Warning("Neural coarse correction and MaxSolveSeconds require a uniform sweep!\n");
  }
  return {adaptive ? SweepAdaptive(space_op) : SweepUniform(space_op),
          space_op.GlobalTrueVSize()};
}

ErrorIndicator DrivenSolver::SweepUniform(SpaceOperator &space_op) const
{
  const auto &port_excitations = space_op.GetPortExcitations();
  const auto &omega_sample = iodata.solver.driven.sample_f;
  const auto comm = space_op.GetComm();
  const char *verify_env = std::getenv("PALACE_VERIFY_RESIDUAL");
  const auto &linear = iodata.solver.linear;
  const auto &settings = linear.neural_coarse;
  int verify_residual =
      settings.Enabled() || (verify_env && std::string_view(verify_env) == "1");
  Mpi::Broadcast(1, &verify_residual, 0, comm);
  const bool right_fgmres = linear.krylov_solver == KrylovSolver::FGMRES &&
                            linear.pc_side != PreconditionerSide::LEFT;
  const bool bounded =
      right_fgmres && Mpi::Size(comm) == 1 && linear.max_solve_seconds > 0.0;
  if (linear.max_solve_seconds > 0.0 && !bounded)
  {
    Mpi::Warning(comm, "MaxSolveSeconds requires single-rank right FGMRES!\n");
  }

  // Initialize postprocessing for measurement and printers.
  // Initialize write directory with default path; will be changed for multi-excitations.
  PostOperator<ProblemType::DRIVEN> post_op(iodata, space_op);

  // The fixed system matrices are only needed when the system cannot be applied through
  // the preconditioner (see SpaceOperator::GetSystemOperator), so assemble them on first
  // use. PEC boundaries are handled simply by setting diagonal entries of the system matrix
  // for the corresponding dofs. Because the Dirichlet BC is always homogeneous, no special
  // elimination is required on the RHS.
  std::unique_ptr<ComplexOperator> K, C, M;
  const auto &Curl = space_op.GetCurlMatrix();

  // Set up the linear solver.
  // The operators are constructed for each frequency step and used to initialize the ksp.
  Timer::TimePoint solve_started{};
  const auto elapsed = [&](Timer::TimePoint start)
  { return Timer::Duration(Timer::Now() - start).count(); };
  const auto deadline_expired = [&]()
  { return elapsed(solve_started) >= linear.max_solve_seconds; };
  const auto trial_expired = [&]()
  { return elapsed(solve_started) >= 0.25 * linear.max_solve_seconds; };
  NeuralCoarseSolver *neural = nullptr;
  NeuralCoarseSolver::BasisBuilder build_basis;
#if defined(PALACE_WITH_ML)
  std::unique_ptr<NeuralModel> model;
  double coarse_omega = 0.0;
  std::string_view unsupported_reason;
  if (settings.Enabled())
  {
    auto &spaces = space_op.GetNDSpaces();
    auto &coarse = spaces.GetFESpaceAtLevel(0);
    if (!bounded || linear.max_it < 2)
    {
      unsupported_reason = "right_fgmres_or_budget";
    }
    else if (spaces.GetNumLevels() < 2 || coarse.IsBroken() ||
             !coarse.GetParMesh().Conforming() || coarse.GetMaxElementOrder() != 1 ||
             !dynamic_cast<const mfem::ND_FECollection *>(&coarse.GetFEColl()))
    {
      unsupported_reason = "coarse_space";
    }
    else if (mfem::Device::Allows(mfem::Backend::HIP_MASK))
    {
      unsupported_reason = "hip_backend";
    }
    else
    {
      build_basis = [&](const ComplexParOperator &, const ComplexLocalCSR &csr,
                        std::span<const int> essential, NeuralCoarseSolver::Basis &basis)
      {
        try
        {
          return BuildNeuralBasis(coarse, linear, csr, essential, coarse_omega,
                                  trial_expired, model, basis);
        }
        catch (const std::exception &e)
        {
          Mpi::Warning(comm, "Neural coarse basis setup failed: {}\n", e.what());
          return false;
        }
      };
    }
  }
#else
  const std::string_view unsupported_reason = settings.Enabled() ? "build_off" : "";
#endif
  if (!unsupported_reason.empty())
  {
    Mpi::Warning(comm, "Neural coarse fallback: {}\n", unsupported_reason);
  }
  auto ksp = std::make_unique<ComplexKspSolver>(iodata, space_op.GetNDSpaces(),
                                                &space_op.GetH1Spaces(),
                                                std::move(build_basis), &neural);

  // Set up RHS vector for the incident field at port boundaries, and the vector for the
  // first frequency step.
  ComplexVector RHS(Curl.Width()), E(Curl.Width()), B(Curl.Height());
  RHS.UseDevice(true);
  E.UseDevice(true);
  B.UseDevice(true);
  E = 0.0;
  B = 0.0;

  // Initialize structures for storing and reducing the results of error estimation.
  const FluxErrorEstimator<ComplexVector> estimator(space_op, iodata);
  ErrorIndicator indicator;

  // If using Floquet BCs, a correction term (kp x E) needs to be added to the B field.
  std::unique_ptr<FloquetCorrSolver<ComplexVector>> floquet_corr;
  if (space_op.GetMaterialOp().HasWaveVector())
  {
    floquet_corr = std::make_unique<FloquetCorrSolver<ComplexVector>>(
        space_op.GetMaterialOp(), space_op.GetNDSpace(), space_op.GetRTSpace(),
        iodata.solver.linear.tol, iodata.solver.linear.max_it, 0);
  }

  // Main excitation and frequency loop.
  auto t0 = Timer::Now();
  std::size_t excitation_counter = 0;
  const std::size_t excitation_restart_counter =
      ((iodata.solver.driven.restart - 1) / omega_sample.size()) + 1;
  const std::size_t freq_restart_idx =
      (iodata.solver.driven.restart - 1) % omega_sample.size();

#if defined(PALACE_WITH_ML)
  std::optional<CaptureOptions> capture_options;
#endif
  if (const char *capture_dir = std::getenv("PALACE_NEURAL_CAPTURE_DIR");
      capture_dir && *capture_dir)
  {
#if defined(PALACE_WITH_ML)
    MFEM_VERIFY(!settings.Enabled() && linear.max_solve_seconds == 0.0 &&
                    Mpi::Size(comm) == 1 && space_op.GetNDSpaces().GetNumLevels() > 1,
                "Neural capture requires an unbounded classical single-rank GMG sweep!");
    capture_options = ConfigureNeuralCapture(capture_dir, iodata, port_excitations,
                                             excitation_restart_counter);
    Mpi::Print(comm, "PALACE_NEURAL_CAPTURE: excitation={} directory={} benchmark=false\n",
               capture_options->excitation, capture_options->directory.string());
#else
    MFEM_ABORT("Neural capture requires a PALACE_WITH_ML build!");
#endif
  }

  // With an initial guess, each solve of an excitation after the first starts from the
  // combination of its solutions at up to num_guess previous frequencies which minimizes
  // ||RHS - A E|| (for the second, the previous solution), which the iterative solver then
  // scales in the norm of its stopping test. Errors of the previous solutions which a
  // left-preconditioned stopping test does not see are carried over, amplified by up to
  // Σⱼ |cⱼ|; in tests, the outputs stayed at the level of the linear solver tolerance.
  // The images A E_prev only exist during the least squares solve. E_prev keeps fewer
  // solutions than the solves of an excitation in this run, and none if it could keep only
  // one.
  constexpr std::size_t num_guess = 4;
  const std::size_t max_solves = (excitation_restart_counter == port_excitations.Size())
                                     ? omega_sample.size() - freq_restart_idx
                                     : omega_sample.size();
  const std::size_t capacity = std::min(num_guess, max_solves - 1);
  linalg::SolutionHistory<ComplexOperator> E_prev(
      (iodata.solver.linear.initial_guess && capacity > 1) ? capacity : 0, E.Size());

  for (const auto &[excitation_idx, excitation_spec] : port_excitations)
  {
    if (++excitation_counter < excitation_restart_counter)
    {
      continue;
    }
    if (port_excitations.Size() > 1)
    {
      Mpi::Print("\nSweeping excitation index {:d} ({:d}/{:d}):\n", excitation_idx,
                 excitation_counter, port_excitations.Size());
    }
    // Start each excitation from zero rather than the previous excitation's solution.
    E = 0.0;
    E_prev.Clear();

    // Frequency loop. Delay the potentially large visualization operators until the
    // first solution is ready, so they do not increase the solve/preconditioner peak.
    const std::size_t omega_start =
        (excitation_counter == excitation_restart_counter) ? freq_restart_idx : 0;
    for (std::size_t omega_i = omega_start; omega_i < omega_sample.size(); omega_i++)
    {
      auto omega = omega_sample[omega_i];
      // Assemble frequency dependent matrices and initialize operators in linear
      // solver. A refers to P and A2, so both must outlive it.
      auto P = space_op.GetPreconditionerMatrix<ComplexOperator>(
          1.0 + 0.0i, 1i * omega, -omega * omega + 0.0i, omega);
      std::unique_ptr<ComplexOperator> A2;
      auto A = space_op.GetSystemOperator(omega, *P);
      if (!A)
      {
        if (!K)
        {
          K = space_op.GetStiffnessMatrix<ComplexOperator>(Operator::DIAG_ONE);
          C = space_op.GetDampingMatrix<ComplexOperator>(Operator::DIAG_ZERO);
          M = space_op.GetMassMatrix<ComplexOperator>(Operator::DIAG_ZERO);
        }
        A2 = space_op.GetExtraSystemOperator(omega, Operator::DIAG_ZERO);
        A = space_op.GetSystemMatrix(1.0 + 0.0i, 1i * omega, -omega * omega + 0.0i, K.get(),
                                     C.get(), M.get(), A2.get());
      }
      if (bounded)
      {
        solve_started = Timer::Now();
      }
#if defined(PALACE_WITH_ML)
      coarse_omega = omega;
      std::unique_ptr<NeuralCapture> capture;
      std::size_t samples = 0;
      if (capture_options && excitation_idx == capture_options->excitation)
      {
        const auto &mg = dynamic_cast<const ComplexMultigridOperator &>(*P);
        const auto &bc = dynamic_cast<const ComplexParOperator &>(mg.GetOperatorAtLevel(0));
        auto &options = *capture_options;
        options.metadata.omega = omega;
        auto limits = options.limits;
        limits.max_bytes = std::min(limits.max_bytes, options.bytes_remaining);
        MFEM_VERIFY(limits.max_bytes >= 4096,
                    "Neural capture exhausted its per-run byte budget!");
        capture = std::make_unique<NeuralCapture>(
            bc, space_op.GetNDSpaces().GetFESpaceAtLevel(0), options.metadata, limits);
        ksp->SetCoarseRhsObserver(
            [&, limit = options.limits.max_samples](const ComplexVector &coarse_rhs)
            {
              if (samples < limit && capture->AppendRhs(coarse_rhs, excitation_idx))
              {
                ++samples;
              }
            });
      }
#endif
      ksp->SetOperators(*A, *P);
      const double setup_s = bounded ? elapsed(solve_started) : 0.0;

      Mpi::Print(
          "\nIt {:d}/{:d}: ω/2π = {:.3e} GHz (total elapsed time = {:.2e} s{})\n",
          omega_i + 1, omega_sample.size(),
          iodata.units.Dimensionalize<Units::ValueType::FREQUENCY>(omega) /
              (2 * std::numbers::pi),
          Timer::Duration(Timer::Now() - t0).count(),
          (port_excitations.Size() > 1)
              ? fmt::format(", solve {:d}/{:d}",
                            1 + omega_i + (excitation_counter - 1) * omega_sample.size(),
                            omega_sample.size() * port_excitations.Size())
              : "");

      // Solve linear system.
      space_op.GetExcitationVector(excitation_idx, omega, RHS);
      const double rhs_norm = verify_residual ? PhysicalNorm(comm, RHS) : 0.0;
      const double epsilon =
          verify_residual ? std::max(ksp->GetAbsTol(), ksp->GetRelTol() * rhs_norm) : 0.0;
      const std::size_t guess_matvecs = E_prev.Size() > 1 ? E_prev.Size() : 0;
      if (guess_matvecs)
      {
        BlockTimer bt(Timer::KSP_INITIAL_GUESS);
        E_prev.MinimalResidualCombination(space_op.GetComm(), *A, RHS, E);
      }

      Mpi::Print("\n");
      std::optional<double> measured;
      bool in_time = true;
      if (bounded)
      {
        // With verification, both phases target the same physical threshold.
        const std::optional<double> threshold =
            verify_residual ? std::optional{epsilon} : std::nullopt;
        int trial_iterations = 0, classical_iterations = 0;
        double trial_s = 0.0, continuation_s = 0.0, residual_s = 0.0,
               classical_setup_s = 0.0;
        std::size_t matvecs = guess_matvecs;
        std::optional<std::size_t> coarse_apps;
        int residual_checks = 0;
        auto measure = [&]()
        {
          const auto start = Timer::Now();
          measured = PhysicalResidual(comm, *A, RHS, E);
          residual_s += elapsed(start);
          residual_checks++;
        };
        std::string_view reason = unsupported_reason;
#if defined(PALACE_WITH_ML)
        const auto *setup_reason = neural ? neural->GetSetupReason() : "classical";
        const int rank = neural ? neural->GetRank() : 0;
        const auto apps_before = neural ? neural->GetNumApplications() : 0;
        const auto classical_setup_before =
            neural ? neural->GetClassicalSetupSeconds() : 0.0;
        bool trial_passed = false, continuation = false;
        if (neural && neural->HasCorrection() && !trial_expired())
        {
          const auto start = Timer::Now();
          if (!linear.initial_guess)
          {
            E = 0.0;
          }
          const ComplexVector initial(E);
          const int limit = std::min(20, std::max(1, linear.max_it / 4));
          const auto guarded_stop = [&]()
          {
            return trial_expired() || neural->HasRequestedClassical() ||
                   neural->GetGuardRejections() >= 2;
          };
          trial_iterations =
              ksp->MultFgmresPhase(RHS, E, limit, epsilon, false, guarded_stop, matvecs);
          trial_s = elapsed(start);
          measure();
          trial_passed = !trial_expired() && ResidualPasses(*measured, rhs_norm, epsilon) &&
                         !neural->HasRequestedClassical() &&
                         neural->GetGuardRejections() < 2;
          if (!trial_passed)
          {
            reason = neural->HasRequestedClassical()     ? neural->GetLastApplyReason()
                     : neural->GetGuardRejections() >= 2 ? "repeated_guard_rejection"
                     : trial_expired()                   ? "trial_deadline"
                                                         : "trial_residual";
            if (!std::isfinite(*measured))
            {
              E = initial;
              measured.reset();
            }
            continuation = true;
          }
        }
        else if (neural)
        {
          reason = neural->HasCorrection() ? "trial_deadline" : setup_reason;
        }
        if (!trial_passed)
#endif
        {
#if defined(PALACE_WITH_ML)
          if (neural)
          {
            neural->UseClassical();
          }
#else
          constexpr bool continuation = false;
#endif
          if (!deadline_expired())
          {
            const auto start = Timer::Now();
            classical_iterations =
                ksp->MultFgmresPhase(RHS, E, linear.max_it - trial_iterations, threshold,
                                     continuation, deadline_expired, matvecs);
            continuation_s = elapsed(start);
            measured.reset();
          }
        }
        ksp->RecordFgmresSolve(trial_iterations + classical_iterations);
        if (verify_residual && !measured)
        {
          measure();
        }
#if defined(PALACE_WITH_ML)
        if (neural)
        {
          coarse_apps = neural->GetNumApplications() - apps_before;
          classical_setup_s = neural->GetClassicalSetupSeconds() - classical_setup_before;
          continuation_s = std::max(0.0, continuation_s - classical_setup_s);
        }
#endif
        in_time = !deadline_expired();
        Mpi::Print(
            comm,
            "PALACE_NEURAL_COARSE: mode={} trial_iterations={} classical_iterations={} "
            "total_iterations={} setup_s={:.9e} trial_s={:.9e} "
            "lazy_classical_setup_s={:.9e} classical_continuation_s={:.9e} "
            "true_residual_s={:.9e} elapsed_s={:.9e} coarse_applications={} "
            "original_A_matvecs={} physical_check_matvecs={} fallback_reason={} "
            "deadline_expired={}\n",
            settings.mode, trial_iterations, classical_iterations,
            trial_iterations + classical_iterations, setup_s, trial_s, classical_setup_s,
            continuation_s, residual_s, elapsed(solve_started),
            coarse_apps ? std::to_string(*coarse_apps) : "unknown",
            matvecs + residual_checks, residual_checks, reason.empty() ? "none" : reason,
            !in_time);
#if defined(PALACE_WITH_ML)
        if (neural)
        {
          Mpi::Print(comm, "PALACE_NEURAL_SETUP: reason={} rank={} guard_rejections={}\n",
                     setup_reason, rank, neural->GetGuardRejections());
        }
#endif
      }
      else
      {
        ksp->Mult(RHS, E);
      }
      if (verify_residual)
      {
        const double residual_norm =
            measured ? *measured : PhysicalResidual(comm, *A, RHS, E);
        const bool passed = ResidualPasses(residual_norm, rhs_norm, epsilon);
        // The legacy marker requires a number in relative=. For a zero RHS the ratio
        // is undefined, and the results reader derives a missing ratio from norm_b=0.
        const bool relative_defined = rhs_norm > 0.0;
        const double relative = relative_defined ? residual_norm / rhs_norm : 0.0;
        Mpi::Print(comm,
                   "PALACE_TRUE_RESIDUAL: norm_Ax_minus_b={:.17e} norm_b={:.17e} "
                   "relative={:.17e} relative_defined={} epsilon={:.17e} "
                   "qualified_linear_solve={}\n",
                   residual_norm, rhs_norm, relative, relative_defined, epsilon, passed);
        if ((!passed || !in_time) && Mpi::Root(comm))
        {
          std::fflush(stdout);
        }
        MFEM_VERIFY(passed, "Physical residual check failed for excitation "
                                << excitation_idx << ", frequency index " << omega_i + 1
                                << ": ||b - A x|| = " << residual_norm
                                << ", epsilon = " << epsilon);
      }
      if (!in_time && !verify_residual)
      {
        std::fflush(stdout);
      }
      MFEM_VERIFY(in_time, "Linear solve exceeded MaxSolveSeconds!");
#if defined(PALACE_WITH_ML)
      if (capture)
      {
        ksp->SetCoarseRhsObserver({});
        if (samples > 0)
        {
          auto &options = *capture_options;
          const auto path =
              options.directory /
              fmt::format("frequency-{}-excitation-{}.json", omega_i + 1, excitation_idx);
          capture->Write(path);
          options.bytes_remaining -= std::filesystem::file_size(path);
          Mpi::Print(comm, "PALACE_NEURAL_CAPTURE: samples={} path={}\n", samples,
                     path.string());
        }
        else
        {
          Mpi::Warning(comm,
                       "No coarse RHS to capture for excitation {}, frequency index {}!\n",
                       excitation_idx, omega_i + 1);
        }
      }
#endif
      E_prev.Push(E);

      if (omega_i + 1 == omega_sample.size() &&
          excitation_counter == port_excitations.Size())
      {
        // That was the last solve: save the solver totals and release the linear solver
        // and system operators, so they do not add to the memory peak of the field output
        // and error estimation which follow.
        SaveMetadata(*ksp);
        ksp.reset();
        E_prev.Release();
        A.reset();
        A2.reset();
        P.reset();
        K.reset();
        C.reset();
        M.reset();
      }

      // Start Post-processing.
      BlockTimer bt0(Timer::POSTPRO);
      Mpi::Print(" Sol. ||E|| = {:.6e} (||RHS|| = {:.6e})\n", linalg::Norml2(comm, E),
                 verify_residual ? rhs_norm : linalg::Norml2(comm, RHS));

      // Compute B = -1/(iω) ∇ x E on the true dofs.
      Curl.Mult(E.Real(), B.Real());
      Curl.Mult(E.Imag(), B.Imag());
      B *= -1.0 / (1i * omega);
      if (space_op.GetMaterialOp().HasWaveVector())
      {
        // Calculate B field correction for Floquet BCs: B += k_F(ω)/ω × E.
        // With k₀ = k_F_ref/ω_ref stored, k_F(ω)/ω = k_F_ref/ω_ref = k₀, so scale = 1.
        floquet_corr->AddMult(
            E, B,
            space_op.GetMaterialOp().HasFloquetFrequencyScaling() ? 1.0 : 1.0 / omega);
      }

      if (omega_i == omega_start)
      {
        // Switch ParaView subfolders once per excitation, after the first solve.
        post_op.InitializeParaviewDataCollection(excitation_idx);
      }
      auto total_domain_energy =
          post_op.MeasureAndPrintAll(excitation_idx, int(omega_i), E, B, omega);

      // Calculate and record the error indicators.
      Mpi::Print(" Updating solution error estimates\n");
      estimator.AddErrorIndicator(E, B, total_domain_energy, omega, indicator);
    }

    // Final postprocessing & printing. After the last excitation, the solver totals were
    // already saved when the solver was released.
    BlockTimer bt0(Timer::POSTPRO);
    if (ksp)
    {
      SaveMetadata(*ksp);
    }
  }
  post_op.MeasureFinalize(indicator);
  return indicator;
}

ErrorIndicator DrivenSolver::SweepAdaptive(SpaceOperator &space_op) const
{
  const auto &port_excitations = space_op.GetPortExcitations();
  const auto &omega_sample = iodata.solver.driven.sample_f;
  // Initialize postprocessing for measurement and printers.
  // Initialize write directory with default path; will be changed for multi-excitations.
  PostOperator<ProblemType::DRIVEN> post_op(iodata, space_op);

  // Configure PROM parameters if not specified.
  double offline_tol = iodata.solver.driven.adaptive_tol;
  std::size_t convergence_memory = iodata.solver.driven.adaptive_memory;
  std::size_t max_size_per_excitation = iodata.solver.driven.adaptive_max_size;
  std::size_t nprom_indices = iodata.solver.driven.prom_indices.size();
  MFEM_VERIFY(max_size_per_excitation <= 0 || max_size_per_excitation >= nprom_indices,
              "Adaptive frequency sweep must sample at least " << nprom_indices
                                                               << " frequency points!");

  // Allocate negative curl matrix for postprocessing the B-field and vectors for the
  // high-dimensional field solution.
  const auto &Curl = space_op.GetCurlMatrix();
  ComplexVector E(Curl.Width()), B(Curl.Height());
  E.UseDevice(true);
  B.UseDevice(true);
  E = 0.0;
  B = 0.0;

  // Initialize structures for storing and reducing the results of error estimation.
  const FluxErrorEstimator<ComplexVector> estimator(space_op, iodata);
  ErrorIndicator indicator;

  // If using Floquet BCs, a correction term (kp x E) needs to be added to the B field.
  std::unique_ptr<FloquetCorrSolver<ComplexVector>> floquet_corr;
  if (space_op.GetMaterialOp().HasWaveVector())
  {
    floquet_corr = std::make_unique<FloquetCorrSolver<ComplexVector>>(
        space_op.GetMaterialOp(), space_op.GetNDSpace(), space_op.GetRTSpace(),
        iodata.solver.linear.tol, iodata.solver.linear.max_it, 0);
  }

  // Configure the PROM operator which performs the parameter space sampling and basis
  // construction during the offline phase as well as the PROM solution during the online
  // phase.
  auto t0 = Timer::Now();
  const double unit_GHz = iodata.units.Dimensionalize<Units::ValueType::FREQUENCY>(1.0) /
                          (2 * std::numbers::pi);
  Mpi::Print("\nBeginning PROM construction offline phase:\n"
             " {:d} points for frequency sweep over [{:.3e}, {:.3e}] GHz\n",
             omega_sample.size(), omega_sample.front() * unit_GHz,
             omega_sample.back() * unit_GHz);
  RomOperator prom_op(iodata, space_op, max_size_per_excitation);
  space_op.GetWavePortOp().SetSuppressOutput(true);
  space_op.GetWavePortOp().ConfigureReducedModelTraining(
      max_size_per_excitation, port_excitations.Size(),
      iodata.solver.driven.adaptive_circuit_synthesis);

  // Add ports to PROM if we do synthesis.
  if (iodata.solver.driven.adaptive_circuit_synthesis)
  {
    prom_op.AddLumpedPortModesForSynthesis();
    if (space_op.GetWavePortOp().Size() > 0)
    {
      // Use the band center as the reference frequency for seeding wave-port modes.
      // The choice rescales the basis vector but does not change correctness.
      const double omega_ref = 0.5 * (omega_sample.front() + omega_sample.back());
      prom_op.AddWavePortModesForSynthesis(omega_ref);
    }
  }

  const auto num_port_modes = prom_op.GetReducedDimension();

  // Initialize the basis with samples from the top and bottom of the frequency
  // range of interest. Each call for an HDM solution adds the frequency sample to P_S and
  // removes it from P \ P_S. Timing for the HDM construction and solve is handled inside
  // of the RomOperator. Returns the relative error of the PROM solution at the sample
  // before the update, from the coefficients of the HDM solution in the updated basis.
  std::size_t num_refined_samples = 0, num_unreproduced = 0;
  auto UpdatePROM = [&](int excitation_idx, double omega, std::size_t sample_idx)
  {
    // Add the HDM solution to the PROM reduced basis, refined if the PROM does not
    // reproduce it (see RomOperator::AddSamplePROM). A certified solution, started from the
    // PROM solution, can be in the span of the basis to round-off (the linear solver barely
    // changed the PROM solution, or took no iteration): such a part adds no basis vector.
    const auto update = prom_op.AddSamplePROM(
        excitation_idx, omega, E,
        fmt::format("sample_e{:d}_s{:d}", excitation_idx, sample_idx), offline_tol);
    if (update.num_refined > 0)
    {
      Mpi::Print(" Refined the sample at ω = {:.3e} GHz {:d} time{}: the PROM did not "
                 "reproduce it to the tolerance{}\n",
                 omega * unit_GHz, update.num_refined, (update.num_refined == 1) ? "" : "s",
                 update.reproduced ? "" : " (and still does not)");
      num_refined_samples++;
    }
    num_unreproduced += !update.reproduced;
    prom_op.UpdateMRI(excitation_idx, omega, update.c);

    // Compute B = -1/(iω) ∇ x E on the true dofs, and set the internal GridFunctions in
    // PostOperator for energy postprocessing and error estimation.
    BlockTimer bt0(Timer::POSTPRO);
    Curl.Mult(E.Real(), B.Real());
    Curl.Mult(E.Imag(), B.Imag());
    B *= -1.0 / (1i * omega);
    if (space_op.GetMaterialOp().HasWaveVector())
    {
      // Calculate B field correction for Floquet BCs: B += k_F(ω)/ω × E.
      // With k₀ = k_F_ref/ω_ref stored, k_F(ω)/ω = k₀, so scale = 1.
      floquet_corr->AddMult(
          E, B, space_op.GetMaterialOp().HasFloquetFrequencyScaling() ? 1.0 : 1.0 / omega);
    }

    // Measure domain energies for the error indicator only. Don't exchange face_nbr_data,
    // unless printing paraview fields.
    auto total_domain_energy = post_op.MeasureDomainFieldEnergyOnly(E, B, omega);
    estimator.AddErrorIndicator(E, B, total_domain_energy, omega, indicator);
    return update.error;
  };

  // Try to certify the PROM at a sample frequency with an HDM solve started from the PROM
  // solution: the PROM is certified if the solve converges (so E is an acceptable HDM
  // solution) with a correction below the tolerance. The solve uses the tighter of the
  // linear solver tolerance and the tolerance of the sweep, so that a PROM solution which
  // only meets a looser linear solver tolerance is not accepted without a correction. The
  // solve is stopped as soon as the correction exceeds the tolerance, since the sample then
  // has to be solved again from zero anyway. Returns the relative correction if certified,
  // and a negative value if not. Eh holds the PROM solution, only with initial guesses.
  const bool initial_guess = iodata.solver.linear.initial_guess;
  const double certification_tol =
      std::min(prom_op.GetLinearSolver().GetRelTol(), offline_tol);
  ComplexVector Eh(initial_guess ? E.Size() : 0);
  Eh.UseDevice(true);
  auto CertifyPROM = [&](int excitation_idx, double omega)
  {
    prom_op.SolvePROM(omega);
    prom_op.ExpandPROMSolution(excitation_idx, Eh);
    if (linalg::Norml2(space_op.GetComm(), Eh) == 0.0)
    {
      return -1.0;
    }
    E = Eh;
    const int num_it = prom_op.GetLinearSolver().NumTotalMultIterations();
    const bool converged = prom_op.SolveHDM(excitation_idx, omega, E, true, offline_tol);
    const int cert_it = prom_op.GetLinearSolver().NumTotalMultIterations() - num_it;
    linalg::AXPY(-1.0, E, Eh);
    const double correction =
        linalg::Norml2(space_op.GetComm(), Eh) / linalg::Norml2(space_op.GetComm(), E);
    const bool certified = converged && correction < offline_tol;
    Mpi::Print("\n Certification from the PROM solution ({:d} iteration{}, tol = {:.3e}): "
               "correction = {:.3e}{}\n",
               cert_it, (cert_it == 1) ? "" : "s", certification_tol, correction,
               certified   ? ", PROM certified"
               : converged ? ", not certified"
                           : ", not certified (solve stopped)");
    return certified ? correction : -1.0;
  };

  // Loop excitations to add to PROM.
  //
  // Restart should not really be used for adaptive sweeps, but must work. Construct PROM in
  // the same way same regardless of restart for consistency. Don't shift excitation start.
  int excitation_counter = 0;
  for (const auto &[excitation_idx, excitation_spec] : port_excitations)
  {
    if (port_excitations.Size() > 1)
    {
      Mpi::Print("\nAdding excitation index {:d} ({:d}/{:d}):\n", excitation_idx,
                 ++excitation_counter, port_excitations.Size());
    }
    // Initialize PROM with explicit HDM samples, record the estimate but do not act on it.
    std::vector<double> max_errors;
    std::size_t counter_rom_sample = 0;
    num_refined_samples = num_unreproduced = 0;
    for (auto i : iodata.solver.driven.prom_indices)
    {
      auto omega = omega_sample[i];
      prom_op.SolveHDM(excitation_idx, omega, E);
      max_errors.push_back(UpdatePROM(excitation_idx, omega, counter_rom_sample++));
    }
    MFEM_VERIFY(prom_op.GetReducedDimension() > num_port_modes,
                "No HDM solution at the initial samples of the adaptive frequency sweep "
                "was added to the PROM basis: they are zero, or in the span of the port "
                "modes to the orthogonalization tolerance!");
    // The estimates associated to the end points are assumed inaccurate.
    max_errors[0] = std::numeric_limits<double>::infinity();
    max_errors[1] = std::numeric_limits<double>::infinity();
    auto memory = std::distance(max_errors.rbegin(),
                                std::find_if(max_errors.rbegin(), max_errors.rend(),
                                             [=](auto x) { return x > offline_tol; }));
    memory = std::max(0L, memory);  // Ensure memory >= 0 as it should be.

    // Greedy procedure for basis construction (offline phase). Basis is initialized with
    // solutions at frequency sweep endpoints and explicit sample frequencies.
    std::size_t it = max_errors.size();
    bool certified_last = false;
    for (std::size_t it0 = it; it < max_size_per_excitation && memory < convergence_memory;
         it++)
    {
      // Compute the location of the maximum error in parameter domain (bounded by the
      // previous samples).
      double omega_star = prom_op.FindMaxError(excitation_idx);

      // Sample HDM and add solution to basis. Basis vectors are solved from zero: a
      // solution started from the PROM solution keeps the error of the PROM in the
      // directions which barely affect the residual of the preconditioned system (weakly
      // excited high-Q modes, for example), and would pollute the basis. With initial
      // guesses, the sample which would complete the convergence memory is first solved
      // from the PROM solution, to certify the PROM there: if the solve converges, to the
      // tighter of the linear solver tolerance and the tolerance of the sweep, with a
      // correction below the tolerance, the PROM solution is within the tolerance of an
      // acceptable HDM solution and the sweep has converged. The certified solution is
      // still added to the basis (unless it is in its span to round-off), as the last
      // sample is without initial guesses: the PROM is then already accurate to the
      // tolerance there, so that the solution only differs from it by a correction below
      // the tolerance. Otherwise, the solve is stopped as soon as the correction exceeds
      // the tolerance, and the sample is solved again from zero (reusing the assembled
      // operators and preconditioner) and added to the basis, as without initial guesses.
      // The error of a certified sample is this correction.
      double error = (initial_guess && memory + 1 == convergence_memory)
                         ? CertifyPROM(excitation_idx, omega_star)
                         : -1.0;
      const bool certified = (error >= 0.0);
      if (!certified)
      {
        prom_op.SolveHDM(excitation_idx, omega_star, E);
      }
      const auto n = prom_op.GetReducedDimension();
      const double update_error =
          UpdatePROM(excitation_idx, omega_star, counter_rom_sample++);
      max_errors.push_back(certified ? error : update_error);
      memory = max_errors.back() < offline_tol ? memory + 1 : 0;

      Mpi::Print("\nGreedy iteration {:d} (n = {:d}): ω* = {:.3e} GHz ({:.3e}), error = "
                 "{:.3e}, memory = {:d}/{:d}{}\n",
                 it - it0 + 1, n, omega_star * unit_GHz, omega_star, max_errors.back(),
                 memory, convergence_memory, certified ? " (certified)" : "");
      certified_last = certified;
    }
    Mpi::Print("\nAdaptive sampling{} {:d} frequency samples:\n"
               " n = {:d}, error = {:.3e}, tol = {:.3e}, memory = {:d}/{:d}\n",
               (it == max_size_per_excitation) ? " reached maximum" : " converged with", it,
               prom_op.GetReducedDimension(), max_errors.back(), offline_tol, memory,
               convergence_memory);
    if (num_refined_samples > 0)
    {
      Mpi::Print(" Samples refined: {:d}, not reproduced after refinement: {:d}\n",
                 num_refined_samples, num_unreproduced);
    }
    if (memory < convergence_memory)
    {
      Mpi::Warning("Adaptive sampling reached \"AdaptiveMaxSamples\" = {:d} before "
                   "converging to \"AdaptiveTol\" = {:.3e} (last error estimate {:.3e}): "
                   "the outputs may not be accurate to the tolerance. Increase "
                   "\"AdaptiveMaxSamples\" or loosen \"AdaptiveTol\"!\n",
                   max_size_per_excitation, offline_tol, max_errors.back());
    }
    if (num_unreproduced > 0)
    {
      Mpi::Warning(
          "The PROM did not reproduce {:d} sample{} to \"AdaptiveTol\" = {:.3e} "
          "even after their refinement: the HDM solutions may not reach this "
          "accuracy, and the outputs near these frequencies may not be accurate to "
          "the tolerance. Loosen \"AdaptiveTol\"!\n",
          num_unreproduced, (num_unreproduced == 1) ? "" : "s", offline_tol);
    }
    utils::PrettyPrint(prom_op.GetSamplePoints(excitation_idx), unit_GHz,
                       " Sampled frequencies (GHz):");
    utils::PrettyPrint(max_errors, 1.0, " Sample errors:");
    if (certified_last)
    {
      Mpi::Print(" Last sample certified: its error is the correction of the PROM solution "
                 "by the linear solver, converged to {:.3e} (zero if no iteration was "
                 "needed)\n",
                 certification_tol);
    }
  }

  prom_op.ReleaseHDMOperators();
  Mpi::Print(" Total offline phase elapsed time: {:.2e} s\n",
             Timer::Duration(Timer::Now() - t0).count());  // Timing on root

  // Circuit synthesis samples the exact cross-section EVP at a tightened tolerance so the
  // fitted pencil does not depend on the port-mode accuracy floor; keep those solves exact
  // (they also enrich the per-port reduced basis).
  if (iodata.solver.driven.adaptive_circuit_synthesis)
  {
    // Project the interface dielectric energy forms of any interface dielectric
    // postprocessing boundaries (config["Boundaries"]["Postprocessing"]["Dielectric"]) onto
    // the basis, for the interface capacitance matrices rom-interface-<index>-C.csv.
    prom_op.PrintPROMMatrices(
        iodata.units, iodata.problem.output,
        post_op.GetInterfaceElectricFieldEnergyMatrices(prom_op.GetBasis()));
  }

  // Exact wave-port modes computed by the HDM samples (and any synthesis samples) have
  // trained a separate per-port reduced eigenspace. Enable guarded Rayleigh-Ritz evaluation
  // for the online output sweep; failed residual checks transparently fall back to the
  // exact port eigensolver and enrich the basis.
  space_op.GetWavePortOp().EnableReducedModel(iodata.solver.driven.adaptive_tol);
  prom_op.PrepareOnlinePhase();
  post_op.ConfigureReducedPostprocessing(prom_op, iodata.solver.driven.adaptive_tol);

  // Main fast frequency sweep loop (online phase).
  Mpi::Print("\nBeginning fast frequency sweep online phase\n");
  space_op.GetWavePortOp().SetSuppressOutput(false);  // Disable output suppression
  auto postprocess_online_point = [&](int excitation_idx, std::size_t omega_i)
  {
    const auto omega = omega_sample[omega_i];
    Mpi::Print("\nIt {:d}/{:d}, excitation {:d}: ω/2π = {:.3e} GHz "
               "(total elapsed time = {:.2e} s)\n",
               omega_i + 1, omega_sample.size(), excitation_idx,
               iodata.units.Dimensionalize<Units::ValueType::FREQUENCY>(omega) /
                   (2 * std::numbers::pi),
               Timer::Duration(Timer::Now() - t0).count());

    // Reduced postprocessing evaluates the outputs from the reduced solution, mostly
    // without expanding it.
    const Eigen::VectorXcd y = prom_op.GetReducedSolution(excitation_idx);
    const bool reduced = post_op.HasReducedPostprocessing() &&
                         !post_op.WillWriteFields(static_cast<int>(omega_i));
    const bool expand = !reduced || post_op.ReducedPostprocessingNeedsField(excitation_idx);
    if (expand)
    {
      prom_op.ExpandPROMSolution(excitation_idx, E);
    }
    Mpi::Print("\n");
    if (omega_i == 0 && post_op.WillWriteFields())
    {
      // Switch ParaView subfolders once per excitation. Delay visualization setup until
      // the first online solution is ready.
      post_op.InitializeParaviewDataCollection(excitation_idx);
    }

    if (reduced)
    {
      post_op.MeasureAndPrintReduced(excitation_idx, int(omega_i), expand ? &E : nullptr,
                                     omega, y, prom_op);
      return;
    }

    // Start full post-processing.
    BlockTimer bt0(Timer::POSTPRO);
    Mpi::Print(" Sol. ||E|| = {:.6e}\n", linalg::Norml2(space_op.GetComm(), E));

    // Compute B = -1/(iω) ∇ x E on the true dofs.
    Curl.Mult(E.Real(), B.Real());
    Curl.Mult(E.Imag(), B.Imag());
    B *= -1.0 / (1i * omega);
    if (space_op.GetMaterialOp().HasWaveVector())
    {
      // Calculate B field correction for Floquet BCs: B += k_F(ω)/ω × E.
      // With k₀ = k_F_ref/ω_ref stored, k_F(ω)/ω = k_F_ref/ω_ref = k₀, so scale = 1.
      floquet_corr->AddMult(
          E, B, space_op.GetMaterialOp().HasFloquetFrequencyScaling() ? 1.0 : 1.0 / omega);
    }
    post_op.MeasureAndPrintAll(excitation_idx, int(omega_i), E, B, omega);
  };

  // The PROM (and the port modes) depend on frequency, not excitation: assemble, factor,
  // and solve it for all excitations once per frequency.
  if (!post_op.WillWriteFields())
  {
    for (std::size_t omega_i = 0; omega_i < omega_sample.size(); omega_i++)
    {
      prom_op.SolvePROM(omega_sample[omega_i]);
      for (const auto &[excitation_idx, excitation_spec] : port_excitations)
      {
        postprocess_online_point(excitation_idx, omega_i);
      }
    }
  }
  else
  {
    // Excitation-major ordering for the excitation-specific field collections.
    for (const auto &[excitation_idx, excitation_spec] : port_excitations)
    {
      if (port_excitations.Size() > 1)
      {
        Mpi::Print("\nSweeping excitation index {:d}:\n", excitation_idx);
      }
      for (std::size_t omega_i = 0; omega_i < omega_sample.size(); omega_i++)
      {
        prom_op.SolvePROM(omega_sample[omega_i]);
        postprocess_online_point(excitation_idx, omega_i);
      }
    }
  }

  // Final postprocessing & printing: no change to indicator since these are in PROM.
  {
    BlockTimer bt0(Timer::POSTPRO);
    SaveMetadata(prom_op.GetLinearSolver());
  }
  space_op.GetWavePortOp().PrintReducedModelStats();
  post_op.MeasureFinalize(indicator);
  return indicator;
}

}  // namespace palace
