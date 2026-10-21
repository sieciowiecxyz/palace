// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include "drivensolver.hpp"

#include <algorithm>
#include <array>
#include <map>
#include <vector>
#include <complex>
#include <cmath>
#include <sstream>
#include <cstdlib>
#include <cstddef>
#include <iostream>
#include <Eigen/Dense>
#include <fmt/core.h>
#include <mfem.hpp>
#include "fem/errorindicator.hpp"
#include "fem/mesh.hpp"
#include "linalg/errorestimator.hpp"
#include "linalg/floquetcorrection.hpp"
#include "linalg/ksp.hpp"
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
#include "utils/coaxdiagnostic.hpp"
#include "utils/fieldcomparison.hpp"
#include "utils/iodata.hpp"
#include "utils/memorymark.hpp"
#include "utils/prettyprint.hpp"
#include "utils/timer.hpp"
#include "utils/sweepprojection.hpp"

extern "C" void PalacePCBasisRelease() __attribute__((weak));

namespace palace
{

using namespace std::complex_literals;

std::pair<ErrorIndicator, long long int>
DrivenSolver::Solve(const std::vector<std::unique_ptr<Mesh>> &mesh) const
{
  // Set up the spatial discretization and frequency sweep.
  BlockTimer bt0(Timer::CONSTRUCT);
  MemoryMark("setup.begin");
  SpaceOperator space_op(iodata, mesh);
  MemoryMark("setup.end");
  const auto &port_excitations = space_op.GetPortExcitations();
  SaveMetadata(port_excitations);

  const auto &omega_sample = iodata.solver.driven.sample_f;

  bool adaptive = (iodata.solver.driven.adaptive_tol > 0.0);
  MFEM_VERIFY(!(std::getenv("PALACE_REUSE_PORT_SETUP") ||
                std::getenv("PALACE_FREQUENCY_PORT_BATCH") ||
                std::getenv("PALACE_SWEEP_PREDICTOR") ||
                std::getenv("PALACE_HISTORY_FIELDS")) || !adaptive,
              "Frequency/port batching requires a uniform sweep!");
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
  auto indicator = adaptive ? SweepAdaptive(space_op) : SweepUniform(space_op);
  MemoryMark("driven.end");
  return {std::move(indicator), space_op.GlobalTrueVSize()};
}

ErrorIndicator DrivenSolver::SweepUniform(SpaceOperator &space_op) const
{
  MemoryMark("operators.begin");
  const auto &port_excitations = space_op.GetPortExcitations();
  const auto &omega_sample = iodata.solver.driven.sample_f;

  // Initialize postprocessing for measurement and printers.
  // Initialize write directory with default path; will be changed for multi-excitations.
  PostOperator<ProblemType::DRIVEN> post_op(iodata, space_op);

  // Construct the system matrices defining the linear operator. PEC boundaries are handled
  // simply by setting diagonal entries of the system matrix for the corresponding dofs.
  // Because the Dirichlet BC is always homogeneous, no special elimination is required on
  // the RHS. Assemble the linear system for the initial frequency (so we can call
  // KspSolver::SetOperators). Compute everything at the first frequency step.
  auto K = space_op.GetStiffnessMatrix<ComplexOperator>(Operator::DIAG_ONE);
  auto C = space_op.GetDampingMatrix<ComplexOperator>(Operator::DIAG_ZERO);
  auto M = space_op.GetMassMatrix<ComplexOperator>(Operator::DIAG_ZERO);
  const auto &Curl = space_op.GetCurlMatrix();

  // Set up the linear solver.
  // The operators are constructed for each frequency step and used to initialize the ksp.
  // Opt-in equal-frequency RHS reuse owns operators longer than the referencing solver.
  std::unique_ptr<ComplexOperator> retained_A2, retained_A, retained_P;
  auto ksp = std::make_unique<ComplexKspSolver>(iodata, space_op.GetNDSpaces(),
                                               &space_op.GetH1Spaces());
  const bool reuse_port_setup = std::getenv("PALACE_REUSE_PORT_SETUP") != nullptr;
  const bool explicit_frequency_batch = std::getenv("PALACE_FREQUENCY_PORT_BATCH") != nullptr;
  const bool frequency_batch = (reuse_port_setup || explicit_frequency_batch) && omega_sample.size() > 1;
  MFEM_VERIFY(!explicit_frequency_batch || omega_sample.size() > 1,
              "Explicit frequency batching requires more than one frequency!");
  const char *predictor_env = std::getenv("PALACE_SWEEP_PREDICTOR");
  const bool sweep_predictor = predictor_env != nullptr;
  const bool project_sweep = predictor_env && std::string(predictor_env) == "projected";
  MFEM_VERIFY(!sweep_predictor || project_sweep || std::string(predictor_env) == "1" ||
                  std::string(predictor_env) == "linear", "Unknown sweep predictor mode!");
  const char *history_source = std::getenv("PALACE_HISTORY_FIELDS");
  std::array<int, 2> history_indices{};
  std::array<double, 2> history_frequencies{};
  if (history_source)
  {
    MFEM_VERIFY(sweep_predictor && omega_sample.size() == 1 && !frequency_batch &&
                    iodata.solver.linear.initial_guess && iodata.solver.driven.restart == 1 &&
                    iodata.model.refinement.max_it == 0 && Mpi::Size(space_op.GetComm()) == 1 &&
                    !post_op.WillWriteFields() && !std::getenv("PALACE_INITIAL_FIELDS") &&
                    space_op.GetWavePortOp().Size() == 0 && space_op.GetFloquetPortOp().Size() == 0,
                "History replay requires a single-frequency uniform rank1 fixed-mesh lumped solve with predictor/InitialGuess, no external seed/viz!");
    const char *indices = std::getenv("PALACE_HISTORY_INDICES");
    const char *frequencies = std::getenv("PALACE_HISTORY_FREQUENCIES");
    MFEM_VERIFY(indices && frequencies, "Missing history frequency/index map!");
    std::istringstream ii(indices), ff(frequencies);
    char comma_i = 0, comma_f = 0, extra = 0;
    MFEM_VERIFY((ii >> history_indices[0] >> comma_i >> history_indices[1]) &&
                    comma_i == ',' && !(ii >> extra) && history_indices[0] >= 0 &&
                    history_indices[1] > history_indices[0], "Invalid history indices!");
    MFEM_VERIFY((ff >> history_frequencies[0] >> comma_f >> history_frequencies[1]) &&
                    comma_f == ',' && !(ff >> extra) && std::isfinite(history_frequencies[0]) &&
                    std::isfinite(history_frequencies[1]) && history_frequencies[0] > 0.0 &&
                    history_frequencies[1] > history_frequencies[0], "Invalid history frequencies!");
    const double target = iodata.units.Dimensionalize<Units::ValueType::FREQUENCY>(omega_sample[0]) / (2 * M_PI);
    MFEM_VERIFY(target > history_frequencies[1], "History must precede the target frequency!");
  }
  MFEM_VERIFY(!sweep_predictor || history_source ||
                  (frequency_batch && omega_sample.size() >= 3 && iodata.solver.linear.initial_guess),
              "Sweep predictor requires >=3 batch frequencies or explicit verified history!");
  const bool setup_audit = reuse_port_setup || explicit_frequency_batch || std::getenv("PALACE_PORT_SETUP_AUDIT");
  const bool release_postprocess_energy = std::getenv("PALACE_RELEASE_POSTPROCESS_ENERGY") != nullptr;
  bool energy_released = false;
  MFEM_VERIFY(!release_postprocess_energy ||
                  (iodata.model.refinement.max_it == 0 && !post_op.WillWriteFields()),
              "Postprocess energy release requires fixed mesh without visualization writes!");
  MFEM_VERIFY(!(reuse_port_setup || frequency_batch) ||
                  ((omega_sample.size() == 1 || port_excitations.Size() == 2) && port_excitations.Size() > 1 && iodata.solver.driven.restart == 1 &&
                   iodata.model.refinement.max_it == 0 && Mpi::Size(space_op.GetComm()) == 1 &&
                   space_op.GetWavePortOp().Size() == 0 && space_op.GetFloquetPortOp().Size() == 0),
              "Port setup reuse requires fixed mesh/rank1/first solve and lumped ports only; multi-frequency batches require exactly two excitations!");
  MFEM_VERIFY(!frequency_batch || !std::getenv("PALACE_INITIAL_FIELDS"),
              "Frequency-major batching uses per-port in-memory history, not external field seeds!");
  MFEM_VERIFY(!frequency_batch || !post_op.WillWriteFields(),
              "Frequency-major batching does not yet support visualization writes!");
  const char *release_env = std::getenv("PALACE_RELEASE_FINAL_SOLVER");
  const bool release_final_solver = release_env && std::string(release_env) == "1";
  MFEM_VERIFY(!release_final_solver || iodata.model.refinement.max_it == 0,
              "Final solver release requires fixed mesh (AMR disabled)!");

  const bool defer_postprocessing = std::getenv("PALACE_DEFER_POSTPROCESSING") != nullptr;
  MFEM_VERIFY(!defer_postprocessing ||
                  (release_final_solver && (omega_sample.size() == 1 || (frequency_batch && release_postprocess_energy)) &&
                   port_excitations.Size() == 2 && iodata.solver.driven.restart == 1 &&
                   Mpi::Size(space_op.GetComm()) == 1 && !post_op.WillWriteFields() &&
                   space_op.GetWavePortOp().Size() == 0 && space_op.GetFloquetPortOp().Size() == 0),
              "Deferred postprocessing requires two lumped excitations, rank1, final solver release and no visualization/wave/Floquet ports; multiple frequencies require frequency-major batching and energy release!");

  // Set up RHS vector for the incident field at port boundaries, and the vector for the
  // first frequency step.
  ComplexVector RHS(Curl.Width()), E(Curl.Width()), B(Curl.Height());
  RHS.UseDevice(true);
  E.UseDevice(true);
  B.UseDevice(true);
  E = 0.0;
  B = 0.0;

  // Initialize structures for storing and reducing the results of error estimation.
  const char *skip_env = std::getenv("PALACE_SKIP_ESTIMATOR");
  const bool skip_estimator = skip_env && skip_env[0] == '1';
  MFEM_VERIFY(!skip_estimator || iodata.model.refinement.max_it == 0,
              "PALACE_SKIP_ESTIMATOR requires fixed mesh (AMR disabled)!");
  if (skip_estimator)
    Mpi::Print("PALACE_EXPERIMENT: error estimator disabled; FEM/GMRES/port outputs unchanged; no estimator qualification\n");
  const bool is_2d = (space_op.GetNDSpace().Dimension() < 3);
  std::unique_ptr<TimeDependentFluxErrorEstimator<ComplexVector>> estimator_3d;
  std::unique_ptr<BoundaryModeFluxErrorEstimator<ComplexVector>> estimator_2d;
  if (!skip_estimator && is_2d)
  {
    estimator_2d = std::make_unique<BoundaryModeFluxErrorEstimator<ComplexVector>>(
        space_op.GetMaterialOp(), space_op.GetNDSpaces(), space_op.GetRTSpaces(),
        space_op.GetCurlSpace(), space_op.GetH1Spaces(), iodata.solver.linear.estimator_tol,
        iodata.solver.linear.estimator_max_it, 0, iodata.solver.linear.estimator_mg);
  }
  else if (!skip_estimator)
  {
    estimator_3d = std::make_unique<TimeDependentFluxErrorEstimator<ComplexVector>>(
        space_op.GetMaterialOp(), space_op.GetNDSpaces(), space_op.GetRTSpaces(),
        iodata.solver.linear.estimator_tol, iodata.solver.linear.estimator_max_it, 0,
        iodata.solver.linear.estimator_mg);
  }
  auto AddEstimate =
      [&](const ComplexVector &E, const ComplexVector &B, double Et, ErrorIndicator &ind)
  {
    if (skip_estimator) return;
    if (is_2d)
      estimator_2d->AddErrorIndicator(E, B, Et, ind);
    else
      estimator_3d->AddErrorIndicator(E, B, Et, ind);
  };
  ErrorIndicator indicator;

  // If using Floquet BCs, a correction term (kp x E) needs to be added to the B field.
  std::unique_ptr<FloquetCorrSolver<ComplexVector>> floquet_corr;
  if (space_op.GetMaterialOp().HasWaveVector())
  {
    floquet_corr = std::make_unique<FloquetCorrSolver<ComplexVector>>(
        space_op.GetMaterialOp(), space_op.GetNDSpace(), space_op.GetRTSpace(),
        iodata.solver.linear.tol, iodata.solver.linear.max_it, 0);
  }

  auto Postprocess = [&](ComplexVector &E, int excitation_idx,
                         std::size_t excitation_counter, std::size_t omega_i,
                         double omega, bool initialize_output, double rhs_norm)
  {
    MemoryMark("postprocess.begin");
    if (energy_released)
    {
      MemoryMark("postprocess_energy_rebuild.begin");
      post_op.ResetDomainEnergyOperators(DomainPostOperator(iodata.domains.postpro,
          space_op.GetMaterialOp(), space_op.GetNDSpace(), space_op.GetCurlSpace()));
      energy_released = false;
      Mpi::Print("PALACE_POSTPROCESS_ENERGY_REBUILT: excitation={} frequency_index={}\n",
                 excitation_idx, omega_i);
      MemoryMark("postprocess_energy_rebuild.end");
    }
    // Start Post-processing.
    BlockTimer bt0(Timer::POSTPRO);
    Mpi::Print(" Sol. ||E|| = {:.6e} (||RHS|| = {:.6e})\n",
               linalg::Norml2(space_op.GetComm(), E),
               rhs_norm);

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

    if (initialize_output)
    {
      // Switch ParaView subfolders once per excitation, after the first solve.
      post_op.InitializeParaviewDataCollection(excitation_idx);
    }
    auto total_domain_energy =
        post_op.MeasureAndPrintAll(excitation_idx, int(omega_i), E, B, omega);
    if (std::getenv("PALACE_COAX_TEM_DIAGNOSTIC"))
    {
      const char *length = std::getenv("PALACE_COAX_TEM_LENGTH_M");
      MFEM_VERIFY(length, "Coax diagnostic requires its validated fixture length!");
      CheckCoaxTEM(post_op.GetEGridFunction(), post_op.GetBGridFunction(), iodata.units,
                   omega, excitation_idx, std::stod(length));
    }
    const char *save_fields = std::getenv("PALACE_SAVE_FIELDS");
    const char *reference_fields = std::getenv("PALACE_REFERENCE_FIELDS");
    if (save_fields || reference_fields)
    {
      MemoryMark("field_diagnostics.begin");
      std::vector<int> regions;
      for (const auto &[idx, data] : iodata.domains.postpro.energy) regions.push_back(idx);
      CompareFieldSnapshots(post_op.GetEGridFunction(), post_op.GetBGridFunction(),
                            post_op.GetDomainPostOperator(), regions, excitation_idx,
                            omega_i, save_fields, reference_fields);
      MemoryMark("field_diagnostics.end");
    }

    // Calculate and record the error indicators.
    Mpi::Print(" Updating solution error estimates\n");
    AddEstimate(E, B, total_domain_energy, indicator);
    MemoryMark("postprocess.end");
    if (release_postprocess_energy &&
        (excitation_counter < port_excitations.Size() || omega_i + 1 < omega_sample.size()))
    {
      MemoryMark("postprocess_energy_release.begin");
      post_op.ResetDomainEnergyOperators();
      energy_released = true;
      Mpi::Print("PALACE_POSTPROCESS_ENERGY_RELEASED: excitation={} frequency_index={}\n",
                 excitation_idx, omega_i);
      MemoryMark("postprocess_energy_release.end");
    }
  };
  // One extra true-DOF E field in RAM/VRAM; no disk-backed solver workspace.
  std::unique_ptr<ComplexVector> deferred_E;
  int deferred_excitation = 0;
  double deferred_rhs_norm = 0.0;

  // Preserve the default excitation-major schedule. Frequency batches visit both
  // RHS before measurements; optional reuse retains only the current LU.
  struct SweepSample { int excitation; std::size_t counter, frequency, start; };
  std::vector<SweepSample> samples;
  const auto restart_counter = ((iodata.solver.driven.restart - 1) / omega_sample.size()) + 1;
  const auto restart_frequency = (iodata.solver.driven.restart - 1) % omega_sample.size();
  std::size_t counter = 0;
  for (const auto &[index, spec] : port_excitations)
  {
    if (++counter < restart_counter) continue;
    const auto start = counter == restart_counter ? restart_frequency : 0;
    for (auto f = start; f < omega_sample.size(); ++f)
      samples.push_back({index, counter, f, start});
  }
  if (frequency_batch)
    std::stable_sort(samples.begin(), samples.end(), [](const auto &a, const auto &b)
                     { return a.frequency < b.frequency; });
  std::map<int, std::unique_ptr<ComplexVector>> sweep_history, sweep_older;
  std::size_t retained_frequency = omega_sample.size();
  int completed_mult = 0, completed_iterations = 0;
  auto t0 = Timer::Now();
  for (const auto &sample : samples)
  {
    const auto excitation_idx = sample.excitation;
    const auto excitation_counter = sample.counter;
    const auto omega_i = sample.frequency;
    const auto omega_start = sample.start;
    if (omega_i == omega_start && port_excitations.Size() > 1)
      Mpi::Print("\nSweeping excitation index {:d} ({:d}/{:d}):\n", excitation_idx,
                 excitation_counter, port_excitations.Size());
    auto omega = omega_sample[omega_i];
    // Assemble frequency dependent matrices and initialize operators in linear
    // solver.
    MemoryMark("preconditioner.begin");
    std::unique_ptr<ComplexOperator> A2, A, P;
    if (!ksp)
      ksp = std::make_unique<ComplexKspSolver>(iodata, space_op.GetNDSpaces(),
                                             &space_op.GetH1Spaces());
    const bool reuse = reuse_port_setup && retained_A && retained_frequency == omega_i;
    if (!reuse)
    {
      A2 = space_op.GetExtraSystemOperator(omega, Operator::DIAG_ZERO);
      A = space_op.GetSystemMatrix(1.0 + 0.0i, 1i * omega, -omega * omega + 0.0i,
                                      K.get(), C.get(), M.get(), A2.get());
      P = space_op.GetPreconditionerMatrix<ComplexOperator>(
        1.0 + 0.0i, 1i * omega, -omega * omega + 0.0i, omega);
      ksp->SetOperators(*A, *P);
      if (reuse_port_setup)
      {
        retained_P.reset(); retained_A.reset(); retained_A2.reset();
        retained_A2 = std::move(A2); retained_A = std::move(A); retained_P = std::move(P);
        retained_frequency = omega_i;
      }
    }
    if (setup_audit)
    {
      Mpi::Print("PALACE_PORT_SETUP: action={} excitation={} frequency_index={}\n",
                 reuse ? "reuse" : "build", excitation_idx, omega_i);
    }
    MemoryMark("preconditioner.end");

    Mpi::Print(
        "\nIt {:d}/{:d}: ω/2π = {:.3e} GHz (total elapsed time = {:.2e} s{})\n",
        omega_i + 1, omega_sample.size(),
        iodata.units.Dimensionalize<Units::ValueType::FREQUENCY>(omega) / (2 * M_PI),
        Timer::Duration(Timer::Now() - t0).count(),
        (port_excitations.Size() > 1)
            ? fmt::format(", solve {:d}/{:d}",
                          1 + omega_i + (excitation_counter - 1) * omega_sample.size(),
                          omega_sample.size() * port_excitations.Size())
            : "");

    if (history_source)
    {
      // Read each immutable source snapshot once. They are inputs, not disk workspace.
      GridFunction field(space_op.GetNDSpace(), true);
      for (int h = 0; h < 2; ++h)
      {
        const auto stem = "s" + std::to_string(excitation_idx) + "-f" +
                          std::to_string(history_indices[h]) + "-E.bin";
        FieldSnapshot(std::filesystem::path(history_source) / stem, field, false);
        auto &destination = h == 0 ? sweep_older[excitation_idx] : sweep_history[excitation_idx];
        destination = std::make_unique<ComplexVector>(E.Size());
        destination->UseDevice(true);
        field.Real().GetTrueDofs(destination->Real());
        field.Imag().GetTrueDofs(destination->Imag());
      }
      E = *sweep_history.at(excitation_idx);
      Mpi::Print("PALACE_HISTORY_SEED: excitation={} frequency_index=0 source_indices={},{} source_frequencies={:.17e},{:.17e} logical_bytes_per_field={}\n",
                 excitation_idx, history_indices[0], history_indices[1], history_frequencies[0],
                 history_frequencies[1], 2LL * sizeof(double) * E.Size());
    }
    // Per-port continuation must not seed port 1 with the last port 2 field.
    if (frequency_batch && iodata.solver.linear.initial_guess)
    {
      auto it = sweep_history.find(excitation_idx);
      if (it == sweep_history.end()) E = 0.0;
      else E = *it->second;
      Mpi::Print("PALACE_SWEEP_SEED: action={} excitation={} frequency_index={}\n",
                 it == sweep_history.end() ? "zero" : "restore", excitation_idx, omega_i);
    }
    // Solve linear system.
    space_op.GetExcitationVector(excitation_idx, omega, RHS);

    if (const char *initial_fields = std::getenv("PALACE_INITIAL_FIELDS"))
    {
      MFEM_VERIFY(Mpi::Size(space_op.GetComm()) == 1 && iodata.solver.linear.initial_guess,
                  "Field restart requires one rank and InitialGuess=true!");
      const char *mask = std::getenv("PALACE_INITIAL_FIELDS_EXCITATIONS");
      const bool seeded = !mask || std::string(mask).find("," + std::to_string(excitation_idx) + ",") != std::string::npos;
      if (seeded)
      {
        GridFunction initial_E(space_op.GetNDSpace(), true);
        const std::string stem = "s" + std::to_string(excitation_idx) + "-f" +
                                 std::to_string(omega_i) + "-E.bin";
        FieldSnapshot(std::filesystem::path(initial_fields) / stem, initial_E, false);
        initial_E.Real().GetTrueDofs(E.Real());
        initial_E.Imag().GetTrueDofs(E.Imag());
        Mpi::Print("PALACE_FIELD_RESTART: excitation={} frequency_index={} norm_E={:.12e}\n",
                   excitation_idx, omega_i, linalg::Norml2(space_op.GetComm(), E));
      }
      else
      {
        E = 0.0;
        Mpi::Print("PALACE_FIELD_RESTART_ZERO: excitation={} frequency_index={}\n", excitation_idx, omega_i);
      }
    }

    if (sweep_predictor && (history_source || omega_i >= 2))
    {
      // Only the initial approximation changes. Compare both starts against the current
      // original FP64 A(f), not the preconditioner, before releasing temporary workspace.
      MemoryMark("sweep_predictor.begin");
      {
        const auto &previous = *sweep_history.at(excitation_idx);
        const auto &older = *sweep_older.at(excitation_idx);
        const double target = iodata.units.Dimensionalize<Units::ValueType::FREQUENCY>(omega) / (2 * M_PI);
        const double ratio = history_source
            ? (target - history_frequencies[1]) / (history_frequencies[1] - history_frequencies[0])
            : (omega_sample[omega_i] - omega_sample[omega_i - 1]) /
              (omega_sample[omega_i - 1] - omega_sample[omega_i - 2]);
        MFEM_VERIFY(std::isfinite(ratio) && ratio > 0.0,
                    "Sweep predictor requires increasing distinct frequencies!");
        const auto &original_A = *(reuse_port_setup ? retained_A : A);
        ComplexVector residual(E.Size());
        residual.UseDevice(true);
        original_A.Mult(E, residual);
        residual.AXPBY(1.0, RHS, -1.0);
        const double baseline = linalg::Norml2(space_op.GetComm(), residual);
        std::complex<double> coefficient = ratio;
        bool coefficient_usable = true;
        if (project_sweep)
        {
          ComplexVector image(E.Size());
          image.UseDevice(true);
          E -= older;
          original_A.Mult(E, image);
          const double image_norm = linalg::Norml2(space_op.GetComm(), image);
          const bool normalizable = image_norm > 0.0 && std::isfinite(image_norm) &&
                                    std::isfinite(1.0 / image_norm);
          std::complex<double> dot = 0.0;
          if (normalizable)
          {
            image *= 1.0 / image_norm;
            // Palace Dot(x,y) = y^H x, so this is (d/||d||)^H r0.
            dot = linalg::Dot(space_op.GetComm(), residual, image);
          }
          auto alpha = normalizable ? SweepProjectionCoefficient(dot, image_norm) : std::nullopt;
          coefficient_usable = alpha.has_value();
          coefficient = alpha.value_or(0.0);
          E = previous;
          Mpi::Print("PALACE_SWEEP_PROJECTION: excitation={} frequency_index={} image_norm={:.17e} dot_real={:.17e} dot_imag={:.17e} alpha_real={:.17e} alpha_imag={:.17e} usable={} operator_applies={}\n",
                     excitation_idx, omega_i, image_norm, dot.real(), dot.imag(),
                     coefficient.real(), coefficient.imag(), coefficient_usable ? 1 : 0,
                     coefficient_usable ? 3 : 2);
        }
        double predicted = baseline;
        if (coefficient_usable)
        {
          E.AXPBY(-coefficient, older, 1.0 + coefficient);
          original_A.Mult(E, residual);
          residual.AXPBY(1.0, RHS, -1.0);
          predicted = linalg::Norml2(space_op.GetComm(), residual);
        }
        const bool accept = std::isfinite(predicted) && predicted < baseline;
        if (!accept) E = previous;
        Mpi::Print("PALACE_SWEEP_PREDICTOR: action={} excitation={} frequency_index={} ratio={:.17e} baseline_residual={:.17e} candidate_residual={:.17e}\n",
                   accept ? "accept" : "fallback", excitation_idx, omega_i, ratio,
                   baseline, predicted);
      }
      MemoryMark("sweep_predictor.end");
    }

    Mpi::Print("\n");
    MemoryMark("gmres.begin");
    ksp->Mult(RHS, E);
    MemoryMark("gmres.end");
    if (frequency_batch && iodata.solver.linear.initial_guess)
    {
      if (omega_i + 1 < omega_sample.size())
      {
        auto &previous = sweep_history[excitation_idx];
        if (!previous)
        {
          previous = std::make_unique<ComplexVector>(E.Size());
          previous->UseDevice(true);
        }
        if (sweep_predictor && omega_i > 0)
        {
          auto &older = sweep_older[excitation_idx];
          if (!older)
          {
            older = std::make_unique<ComplexVector>(E.Size());
            older->UseDevice(true);
          }
          *older = *previous;
          Mpi::Print("PALACE_SWEEP_OLDER: action=store excitation={} frequency_index={} logical_bytes={}\n",
                     excitation_idx, omega_i, 2LL * sizeof(double) * E.Size());
        }
        *previous = E;
        Mpi::Print("PALACE_SWEEP_SEED: action=store excitation={} frequency_index={} logical_bytes={}\n",
                   excitation_idx, omega_i, 2LL * sizeof(double) * E.Size());
      }
      else
      {
        sweep_history.erase(excitation_idx);
        if (sweep_predictor)
        {
          MFEM_VERIFY(sweep_older.erase(excitation_idx) == 1, "Missing older sweep history!");
          Mpi::Print("PALACE_SWEEP_OLDER: action=release excitation={} frequency_index={}\n",
                     excitation_idx, omega_i);
        }
        Mpi::Print("PALACE_SWEEP_SEED: action=release excitation={} frequency_index={}\n",
                   excitation_idx, omega_i);
      }
    }

    if (history_source)
    {
      sweep_history.erase(excitation_idx);
      sweep_older.erase(excitation_idx);
      Mpi::Print("PALACE_HISTORY_RELEASE: excitation={} frequency_index=0\n", excitation_idx);
    }

    // Release current factors before deferred measurements; K/C/M remain for the next f.
    const bool last_rhs = excitation_counter == port_excitations.Size();
    const bool final_sample = last_rhs && omega_i + 1 == omega_sample.size();
    const bool frequency_release = frequency_batch && defer_postprocessing && last_rhs;
    if (release_final_solver && (final_sample || frequency_release))
    {
      if (final_sample) MemoryMark("linear_workspace_release.begin");
      if (frequency_release) MemoryMark("frequency_workspace_release.begin");
      completed_mult += ksp->NumTotalMult();
      completed_iterations += ksp->NumTotalMultIterations();
      SaveLinearSolverMetadata(completed_mult, completed_iterations);
      ksp.reset();
      A.reset();
      P.reset();
      A2.reset();
      retained_P.reset(); retained_A.reset(); retained_A2.reset();
      if (frequency_release)
      {
        Mpi::Print("PALACE_FREQUENCY_SOLVER_RELEASED: frequency_index={} solves_so_far={} iterations_so_far={}\n",
                   omega_i, completed_mult, completed_iterations);
        MemoryMark("frequency_workspace_release.end");
      }
      if (final_sample)
      {
        K.reset();
        C.reset();
        M.reset();
        const char *pc_basis = std::getenv("PALACE_PC_BASIS_FP32_FORWARD");
        const char *pc_compensated = std::getenv("PALACE_PC_BASIS_COMPENSATED_FORWARD");
        if ((pc_basis && std::string(pc_basis) == "1") ||
            (pc_compensated && std::string(pc_compensated) == "1"))
        {
          MFEM_VERIFY(PalacePCBasisRelease, "Mixed PC basis requires its release hook!");
          PalacePCBasisRelease();
        }
        Mpi::Print("PALACE_FINAL_SOLVER_RELEASED: enabled=1\n");
        MemoryMark("linear_workspace_release.end");
      }
    }

    const double rhs_norm = linalg::Norml2(space_op.GetComm(), RHS);
    if (defer_postprocessing && excitation_counter == 1)
    {
      deferred_E = std::make_unique<ComplexVector>(E.Size());
      deferred_E->UseDevice(true);
      *deferred_E = E;
      deferred_excitation = excitation_idx;
      deferred_rhs_norm = rhs_norm;
      Mpi::Print("PALACE_DEFERRED_POSTPROCESS: action=store excitation={} frequency_index={} logical_bytes={}\n",
                 excitation_idx, omega_i, 2LL * sizeof(double) * E.Size());
    }
    else
    {
      if (deferred_E)
      {
        MFEM_VERIFY(!ksp, "Deferred measurements must follow final solver destruction!");
        Mpi::Print("PALACE_DEFERRED_POSTPROCESS: action=measure excitation={} frequency_index={}\n",
                   deferred_excitation, omega_i);
        Postprocess(*deferred_E, deferred_excitation, 1, omega_i, omega, omega_i == omega_start, deferred_rhs_norm);
        deferred_E.reset();
      }
      if (defer_postprocessing)
        Mpi::Print("PALACE_DEFERRED_POSTPROCESS: action=measure excitation={} frequency_index={}\n",
                   excitation_idx, omega_i);
      Postprocess(E, excitation_idx, excitation_counter, omega_i, omega,
                  omega_i == omega_start, rhs_norm);
    }
  }
  MFEM_VERIFY(sweep_history.empty() && sweep_older.empty(), "Unreleased frequency-sweep history!");
  if (ksp) SaveMetadata(*ksp);
  post_op.MeasureFinalize(indicator);
  return indicator;
}

ErrorIndicator DrivenSolver::SweepAdaptive(SpaceOperator &space_op) const
{
  const auto &port_excitations = space_op.GetPortExcitations();
  const auto &omega_sample = iodata.solver.driven.sample_f;
  const bool validate_prom = std::getenv("PALACE_PROM_VALIDATE") != nullptr;
  MFEM_VERIFY(!validate_prom || (Mpi::Size(space_op.GetComm()) == 1 &&
                  iodata.model.refinement.max_it == 0 && iodata.solver.driven.save_indices.empty() &&
                  space_op.GetWavePortOp().Size() == 0 && space_op.GetFloquetPortOp().Size() == 0),
              "PROM validation requires a rank1 fixed-mesh lumped sweep without visualization!");

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
  ComplexVector E(Curl.Width()), Eh(Curl.Width()), B(Curl.Height());
  E.UseDevice(true);
  Eh.UseDevice(true);
  B.UseDevice(true);
  E = 0.0;
  Eh = 0.0;
  B = 0.0;

  // Initialize structures for storing and reducing the results of error estimation.
  const bool is_2d = (space_op.GetNDSpace().Dimension() < 3);
  std::unique_ptr<TimeDependentFluxErrorEstimator<ComplexVector>> estimator_3d;
  std::unique_ptr<BoundaryModeFluxErrorEstimator<ComplexVector>> estimator_2d;
  const bool skip_estimator = std::getenv("PALACE_SKIP_ESTIMATOR") != nullptr;
  if (!skip_estimator && is_2d)
  {
    estimator_2d = std::make_unique<BoundaryModeFluxErrorEstimator<ComplexVector>>(
        space_op.GetMaterialOp(), space_op.GetNDSpaces(), space_op.GetRTSpaces(),
        space_op.GetCurlSpace(), space_op.GetH1Spaces(), iodata.solver.linear.estimator_tol,
        iodata.solver.linear.estimator_max_it, 0, iodata.solver.linear.estimator_mg);
  }
  else if (!skip_estimator)
  {
    estimator_3d = std::make_unique<TimeDependentFluxErrorEstimator<ComplexVector>>(
        space_op.GetMaterialOp(), space_op.GetNDSpaces(), space_op.GetRTSpaces(),
        iodata.solver.linear.estimator_tol, iodata.solver.linear.estimator_max_it, 0,
        iodata.solver.linear.estimator_mg);
  }
  auto AddEstimate =
      [&](const ComplexVector &E, const ComplexVector &B, double Et, ErrorIndicator &ind)
  {
    if (skip_estimator) return;
    if (is_2d)
      estimator_2d->AddErrorIndicator(E, B, Et, ind);
    else
      estimator_3d->AddErrorIndicator(E, B, Et, ind);
  };
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
  const double unit_GHz =
      iodata.units.Dimensionalize<Units::ValueType::FREQUENCY>(1.0) / (2 * M_PI);
  Mpi::Print("\nBeginning PROM construction offline phase:\n"
             " {:d} points for frequency sweep over [{:.3e}, {:.3e}] GHz\n",
             omega_sample.size(), omega_sample.front() * unit_GHz,
             omega_sample.back() * unit_GHz);
  RomOperator prom_op(iodata, space_op, max_size_per_excitation);
  space_op.GetWavePortOp().SetSuppressOutput(true);

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

  // Initialize the basis with samples from the top and bottom of the frequency
  // range of interest. Each call for an HDM solution adds the frequency sample to P_S and
  // removes it from P \ P_S. Timing for the HDM construction and solve is handled inside
  // of the RomOperator.
  auto UpdatePROM = [&](int excitation_idx, double omega, std::size_t sample_idx)
  {
    // Add the HDM solution to the PROM reduced basis.
    prom_op.UpdatePROM(E, fmt::format("sample_e{:d}_s{:d}", excitation_idx, sample_idx));
    prom_op.UpdateMRI(excitation_idx, omega, E);
    if (validate_prom)
      Mpi::Print("PALACE_PROM_SAMPLE: excitation={} frequency_ghz={:.17e}\n",
                 excitation_idx, omega * unit_GHz);

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
    auto total_domain_energy = post_op.MeasureDomainFieldEnergyOnly(E, B);
    AddEstimate(E, B, total_domain_energy, indicator);
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
    prom_op.SetExcitationIndex(excitation_idx);  // Pre-compute RHS1

    // Initialize PROM with explicit HDM samples, record the estimate but do not act on it.
    std::vector<double> max_errors;
    std::size_t counter_rom_sample = 0;
    for (auto i : iodata.solver.driven.prom_indices)
    {
      auto omega = omega_sample[i];
      prom_op.SolveHDM(excitation_idx, omega, E);
      prom_op.SolvePROM(excitation_idx, omega, Eh);
      linalg::AXPY(-1.0, E, Eh);
      max_errors.push_back(linalg::Norml2(space_op.GetComm(), Eh) /
                           linalg::Norml2(space_op.GetComm(), E));
      UpdatePROM(excitation_idx, omega, counter_rom_sample);
      counter_rom_sample++;
    }
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
    for (std::size_t it0 = it; it < max_size_per_excitation && memory < convergence_memory;
         it++)
    {
      // Compute the location of the maximum error in parameter domain (bounded by the
      // previous samples).
      double omega_star = prom_op.FindMaxError(excitation_idx)[0];

      // Sample HDM and add solution to basis.
      prom_op.SolveHDM(excitation_idx, omega_star, E);
      prom_op.SolvePROM(excitation_idx, omega_star, Eh);
      linalg::AXPY(-1.0, E, Eh);

      max_errors.push_back(linalg::Norml2(space_op.GetComm(), Eh) /
                           linalg::Norml2(space_op.GetComm(), E));
      memory = max_errors.back() < offline_tol ? memory + 1 : 0;

      Mpi::Print("\nGreedy iteration {:d} (n = {:d}): ω* = {:.3e} GHz ({:.3e}), error = "
                 "{:.3e}, memory = {:d}/{:d}\n",
                 it - it0 + 1, prom_op.GetReducedDimension(), omega_star * unit_GHz,
                 omega_star, max_errors.back(), memory, convergence_memory);
      UpdatePROM(excitation_idx, omega_star, counter_rom_sample);
      counter_rom_sample++;
    }
    Mpi::Print("\nAdaptive sampling{} {:d} frequency samples:\n"
               " n = {:d}, error = {:.3e}, tol = {:.3e}, memory = {:d}/{:d}\n",
               (it == max_size_per_excitation) ? " reached maximum" : " converged with", it,
               prom_op.GetReducedDimension(), max_errors.back(), offline_tol, memory,
               convergence_memory);
    utils::PrettyPrint(prom_op.GetSamplePoints(excitation_idx), unit_GHz,
                       " Sampled frequencies (GHz):");
    utils::PrettyPrint(max_errors, 1.0, " Sample errors:");
  }

  Mpi::Print(" Total offline phase elapsed time: {:.2e} s\n",
             Timer::Duration(Timer::Now() - t0).count());  // Timing on root

  if (iodata.solver.driven.adaptive_circuit_synthesis)
  {
    prom_op.PrintPROMMatrices(iodata.units, iodata.problem.output);
  }

  // Main fast frequency sweep loop (online phase).
  Mpi::Print("\nBeginning fast frequency sweep online phase\n");
  space_op.GetWavePortOp().SetSuppressOutput(false);  // Disable output suppression
  excitation_counter = 0;
  for (const auto &[excitation_idx, excitation_spec] : port_excitations)
  {
    if (port_excitations.Size() > 1)
    {
      Mpi::Print("\nSweeping excitation index {:d} ({:d}/{:d}):\n", excitation_idx,
                 ++excitation_counter, port_excitations.Size());
    }
    // Frequency loop. Delay visualization setup until the first online solution is ready.
    for (std::size_t omega_i = 0; omega_i < omega_sample.size(); omega_i++)
    {
      auto omega = omega_sample[omega_i];
      Mpi::Print("\nIt {:d}/{:d}: ω/2π = {:.3e} GHz (total elapsed time = {:.2e} s)\n",
                 omega_i + 1, omega_sample.size(),
                 iodata.units.Dimensionalize<Units::ValueType::FREQUENCY>(omega) /
                     (2 * M_PI),
                 Timer::Duration(Timer::Now() - t0).count());

      // Assemble and solve the PROM linear system.
      prom_op.SolvePROM(excitation_idx, omega, E);
      if (validate_prom)
      {
        const double relative = prom_op.OriginalRelativeResidual(excitation_idx, omega, E);
        const auto &samples = prom_op.GetSamplePoints(excitation_idx);
        const bool training = std::any_of(samples.begin(), samples.end(), [omega](double f)
        { return std::abs(f - omega) <= 1e-12 * std::abs(omega); });
        Mpi::Print("PALACE_PROM_RAW: excitation={} frequency_index={} training={} "
                   "dimension={} relative={:.12e}\n",
                   excitation_idx, omega_i, int(training), prom_op.GetReducedDimension(), relative);
      }
      Mpi::Print("\n");

      // Start Post-processing.
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
            E, B,
            space_op.GetMaterialOp().HasFloquetFrequencyScaling() ? 1.0 : 1.0 / omega);
      }
      if (omega_i == 0)
      {
        // Switch ParaView subfolders once per excitation, after the first solve.
        post_op.InitializeParaviewDataCollection(excitation_idx);
      }
      post_op.MeasureAndPrintAll(excitation_idx, int(omega_i), E, B, omega);
      if (validate_prom)
      {
        std::vector<int> regions;
        for (const auto &[idx, data] : iodata.domains.postpro.energy) regions.push_back(idx);
        CompareFieldSnapshots(post_op.GetEGridFunction(), post_op.GetBGridFunction(),
                              post_op.GetDomainPostOperator(), regions, excitation_idx,
                              omega_i, std::getenv("PALACE_SAVE_FIELDS"),
                              std::getenv("PALACE_REFERENCE_FIELDS"));
      }
    }

    // Final postprocessing & printing: no change to indicator since these are in PROM.
    BlockTimer bt0(Timer::POSTPRO);
    SaveMetadata(prom_op.GetLinearSolver());
  }
  post_op.MeasureFinalize(indicator);
  return indicator;
}

}  // namespace palace
