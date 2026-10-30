// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Standalone geometry diagnostic, never a Maxwell solve or a GSLIB fallback.
// Usage: stage-probe-locator CONFIG REPORT HOST-VERIFIED-IDENTITY.json
// Run in a new case directory with the original relative mesh path and fresh output.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
#include <mfem.hpp>
#include <nlohmann/json.hpp>
#include "drivers/drivensolver.hpp"
#include "fem/libceed/ceed.hpp"
#include "fem/mesh.hpp"
#include "fem/probelocator.hpp"
#include "linalg/hypre.hpp"
#include "utils/communication.hpp"
#include "utils/geodata.hpp"
#include "utils/iodata.hpp"
#include "utils/omp.hpp"
#include "utils/outputdir.hpp"
#include "utils/units.hpp"

namespace
{
using json = nlohmann::json;
using Clock = std::chrono::steady_clock;

struct TimePoint
{
  Clock::time_point wall = Clock::now();
  std::clock_t cpu = std::clock();
  json Elapsed() const
  {
    return {{"wall_s", std::chrono::duration<double>(Clock::now() - wall).count()},
            {"process_cpu_s", double(std::clock() - cpu) / CLOCKS_PER_SEC}};
  }
};

void Require(bool condition, const char *message)
{
  if (!condition)
  {
    throw std::runtime_error(message);
  }
}

json Locate(mfem::ParMesh &mesh, mfem::DenseMatrix &points,
            const std::vector<int> &probe_ids, const char *name,
            mfem::InverseElementTransformation::InitGuessType guess)
{
  using Inverse = mfem::InverseElementTransformation;
  const long sequence = mesh.GetSequence(), nodes_sequence = mesh.GetNodesSequence();
  Inverse inverse;
  inverse.SetInitialGuessType(guess);
  inverse.SetSolverType(Inverse::NewtonElementProject);
  inverse.SetReferenceTol(1.0e-15);
  inverse.SetPhysicalRelTol(4.0e-15);
  inverse.SetElementTol(1.0e-8);
  inverse.SetMaxIter(16);
  // All modes use the same default initial-guess grid; no iteration/tolerance changes.
  inverse.SetInitGuessPointsType(mfem::Quadrature1D::OpenHalfUniform);
  inverse.SetInitGuessRelOrder(-1);
  mfem::Array<int> elements;
  mfem::Array<mfem::IntegrationPoint> references;
  const TimePoint start;
  const int found =
      mesh.mfem::Mesh::FindPoints(points, elements, references, false, &inverse);
  json attempt = start.Elapsed();
  attempt["method"] = name;
  attempt["initial_guess_enum"] = static_cast<int>(guess);
  attempt["found"] = found;
  attempt["missing_ids"] = json::array();
  attempt["boundary_ids"] = json::array();
  attempt["bad_forward_residual_ids"] = json::array();
  attempt["points"] = json::array();
  mfem::Vector mapped(3);
  double maximum_residual = 0.0;
  for (int i = 0; i < points.Width(); i++)
  {
    json point = {{"id", probe_ids[i]},
                  {"element", elements[i]},
                  {"normalized_center", {points(0, i), points(1, i), points(2, i)}}};
    if (elements[i] < 0)
    {
      attempt["missing_ids"].push_back(probe_ids[i]);
      point["reference"] = nullptr;  // MFEM leaves missing-point references unspecified.
    }
    else
    {
      const auto &ip = references[i];
      const auto geometry = mesh.GetElementBaseGeometry(elements[i]);
      mesh.GetElementTransformation(elements[i])->Transform(ip, mapped);
      double residual = 0.0, scale = 1.0;
      bool finite = true;
      for (int d = 0; d < 3; d++)
      {
        finite = finite && std::isfinite(mapped(d)) && std::isfinite(points(d, i));
        residual = std::max(residual, std::abs(mapped(d) - points(d, i)));
        scale = std::max(scale, std::abs(points(d, i)));
      }
      const bool strict = mfem::Geometry::CheckPoint(geometry, ip, -1.0e-7);
      const bool good_residual = finite && residual <= 1.0e-12 * scale;
      point["reference"] = {ip.x, ip.y, ip.z};
      point["geometry_type"] = static_cast<int>(geometry);
      point["mapped_center"] = {mapped(0), mapped(1), mapped(2)};
      point["strict_interior"] = strict;
      point["forward_residual_linf"] = finite ? json(residual) : json(nullptr);
      point["forward_residual_limit"] = 1.0e-12 * scale;
      point["forward_residual_pass"] = good_residual;
      maximum_residual = std::max(maximum_residual, residual);
      if (!strict)
      {
        attempt["boundary_ids"].push_back(probe_ids[i]);
      }
      if (!good_residual)
      {
        attempt["bad_forward_residual_ids"].push_back(probe_ids[i]);
      }
    }
    attempt["points"].push_back(std::move(point));
  }
  attempt["max_forward_residual_linf"] = maximum_residual;
  attempt["qualifies_conservative_fast_path"] = found == points.Width() &&
                                                attempt["boundary_ids"].empty() &&
                                                attempt["bad_forward_residual_ids"].empty();
  Require(mesh.GetSequence() == sequence && mesh.GetNodesSequence() == nodes_sequence,
          "Location unexpectedly changed the mesh revision");
  return attempt;
}

json BroadenCandidates(mfem::ParMesh &mesh, mfem::DenseMatrix &points,
                       const std::vector<int> &probe_ids, const json &center_result)
{
  using namespace palace::fem::probe;
  const long sequence = mesh.GetSequence(), nodes_sequence = mesh.GetNodesSequence();
  const TimePoint total;
  mfem::Array<int> elements(points.Width());
  mfem::Array<mfem::IntegrationPoint> references(points.Width());
  for (int i = 0; i < points.Width(); i++)
  {
    elements[i] = center_result["points"][i]["element"].get<int>();
    if (elements[i] >= 0)
    {
      const auto &reference = center_result["points"][i]["reference"];
      references[i].Set3(reference[0].get<double>(), reference[1].get<double>(),
                         reference[2].get<double>());
    }
  }
  std::vector<Trace> trace;
  const auto stats = Rescue(mesh, points, elements, references, &trace);
  json result = {
      {"method", "CenterWith128ElementCenterCandidates"},
      {"candidate_cap", CandidateCap},
      {"source_method", "Center"},
      {"missing_input_count", points.Width() - stats.initial_found},
      {"distance_metric", "Euclidean, lexicographic element-ID tie"},
      {"initial_guess", "Center"},
      {"max_iterations", 16},
      {"precision_and_tolerances_changed", false},
      {"rescued_ids", json::array()},
      {"unresolved_ids", json::array()},
      {"points", json::array()},
      {"mesh_nonconforming", mesh.Nonconforming()},
      {"element_center_evaluations", stats.center_evaluations},
      {"distance_evaluations", static_cast<long long>(stats.center_evaluations) *
                                   (points.Width() - stats.initial_found)},
      {"candidate_storage_entries_bound",
       CandidateCap * (points.Width() - stats.initial_found)},
      {"selection",
       {{"wall_s", stats.selection_wall_s}, {"process_cpu_s", stats.selection_cpu_s}}},
      {"inversion",
       {{"wall_s", stats.inverse_wall_s}, {"process_cpu_s", stats.inverse_cpu_s}}}};
  // Evidence reconstruction is diagnostic-only; the production helper has no table/logs.
  std::unique_ptr<mfem::Table> vertex_elements;
  if (!trace.empty())
  {
    vertex_elements.reset(mesh.GetVertexToElementTable());
  }
  for (const auto &evidence : trace)
  {
    const int i = evidence.point;
    std::vector<int> baseline_candidates;
    if (!evidence.candidates.empty())
    {
      const int closest = evidence.candidates.front().second;
      baseline_candidates.push_back(closest);
      mfem::Array<int> vertices;
      mesh.GetElementVertices(closest, vertices);
      for (const int vertex : vertices)
      {
        const int *row = vertex_elements->GetRow(vertex);
        baseline_candidates.insert(baseline_candidates.end(), row,
                                   row + vertex_elements->RowSize(vertex));
      }
      std::sort(baseline_candidates.begin(), baseline_candidates.end());
      baseline_candidates.erase(
          std::unique(baseline_candidates.begin(), baseline_candidates.end()),
          baseline_candidates.end());
    }
    json point = {{"id", probe_ids[i]},
                  {"candidate_ids", json::array()},
                  {"tested", json::array()},
                  {"qualifying_element", nullptr},
                  {"baseline_vertex_neighborhood", baseline_candidates}};
    for (const auto &candidate : evidence.candidates)
    {
      point["candidate_ids"].push_back(candidate.second);
    }
    for (const auto &trial : evidence.tried)
    {
      json tested = {{"element", trial.element},
                     {"center_distance", trial.distance},
                     {"inverse_status", trial.status}};
      if (trial.status == mfem::InverseElementTransformation::Inside)
      {
        tested["reference"] = {trial.reference.x, trial.reference.y, trial.reference.z};
        tested["strict_interior"] = trial.quality.strict;
        tested["forward_residual_linf"] =
            trial.quality.finite ? json(trial.quality.residual) : json(nullptr);
        tested["forward_residual_pass"] = trial.quality.forward;
      }
      point["tested"].push_back(std::move(tested));
    }
    const bool rescued = elements[i] >= 0;
    if (rescued)
    {
      const auto &ip = references[i];
      point["qualifying_element"] = elements[i];
      point["reference"] = {ip.x, ip.y, ip.z};
      point["center_rank"] = evidence.tried.size();
      const bool outside = !std::binary_search(baseline_candidates.begin(),
                                               baseline_candidates.end(), elements[i]);
      point["outside_baseline_vertex_neighborhood"] = outside;
      point["proves_candidate_neighborhood_issue"] = outside && !mesh.Nonconforming();
    }
    point["candidates_tested"] = evidence.tried.size();
    result[rescued ? "rescued_ids" : "unresolved_ids"].push_back(probe_ids[i]);
    result["points"].push_back(std::move(point));
  }
  result["whole_batch_qualifies_conservative_fast_path"] =
      stats.remaining == 0 && center_result["boundary_ids"].empty() &&
      center_result["bad_forward_residual_ids"].empty();
  result["total"] = total.Elapsed();
  Require(mesh.GetSequence() == sequence && mesh.GetNodesSequence() == nodes_sequence,
          "Candidate search unexpectedly changed the mesh revision");
  return result;
}

void Run(const char *config_path, const char *report_path, const char *identity_path,
         int threads)
{
  using namespace palace;
  MPI_Comm comm = Mpi::World();
  static_assert(sizeof(mfem::real_t) == sizeof(double), "Diagnostic requires FP64 MFEM");
  Require(Mpi::Size(comm) == 1, "Locator diagnostic requires one MPI rank");
  Require(threads == 1, "Locator diagnostic requires OMP_NUM_THREADS=1");
  Require(!fs::exists(report_path),
          "Report already exists; do not overwrite prior evidence");
  std::ifstream identity_file(identity_path);
  Require(bool(identity_file), "Cannot open host-verified input identity");
  json report = {
      {"schema", 1},
      {"diagnostic_only", true},
      {"rf_result", false},
      {"solve_executed", false},
      {"gslib_setup_executed", false},
      {"runtime_device", "cpu,omp"},
      {"ranks", 1},
      {"threads", threads},
      {"config_path", config_path},
      {"provided_input_identity", json::parse(identity_file)},
      {"identity_scope", "Host runner must verify input SHA before and after execution"}};
  const TimePoint total;
  IoData iodata(config_path, false);
  Require(iodata.problem.type == ProblemType::DRIVEN &&
              iodata.model.refinement.max_it == 0 &&
              iodata.solver.driven.adaptive_tol <= 0.0,
          "Diagnostic requires driven uniform fixed mesh");
  // BaseSolver writes metadata in its constructor, so insist on a fresh case output.
  Require(!fs::exists(iodata.problem.output), "Use a fresh Problem.Output directory");
  MakeOutputFolder(iodata, comm);
  const auto original_probes = iodata.domains.postpro.probe;
  DrivenSolver solver(iodata, true, 1, threads, nullptr);
  TimePoint phase;
  auto serial_mesh = mesh::Load(iodata, comm);
  report["pipeline"]["load"] = phase.Elapsed();
  phase = TimePoint{};
  solver.Preprocess(iodata, serial_mesh, comm);
  report["pipeline"]["driver_preprocess_units"] = phase.Elapsed();
  std::vector<std::unique_ptr<mfem::ParMesh>> mfem_mesh;
  phase = TimePoint{};
  mfem_mesh.push_back(mesh::Partition(iodata, std::move(serial_mesh), comm));
  report["pipeline"]["partition"] = phase.Elapsed();
  phase = TimePoint{};
  mesh::RefineMesh(iodata, mfem_mesh);
  report["pipeline"]["refine"] = phase.Elapsed();
  phase = TimePoint{};
  std::vector<std::unique_ptr<Mesh>> wrapped;
  for (auto &m : mfem_mesh)
  {
    wrapped.push_back(std::make_unique<Mesh>(std::move(m)));
  }
  report["pipeline"]["mesh_wrappers_ensure_nodes"] = phase.Elapsed();
  auto &mesh = wrapped.back()->Get();
  Require(mesh.Dimension() == 3 && mesh.SpaceDimension() == 3, "Requires volume 3D mesh");
  Require(mesh.GetNodes() != nullptr, "Production wrapper must ensure geometry nodes");
  report["mesh"] = {{"elements", mesh.GetNE()},
                    {"vertices", mesh.GetNV()},
                    {"boundary_elements", mesh.GetNBE()},
                    {"curvature_order", mesh.GetNodes()->FESpace()->GetMaxElementOrder()},
                    {"sequence", mesh.GetSequence()},
                    {"nodes_sequence", mesh.GetNodesSequence()},
                    {"mesh_levels", wrapped.size()}};
  report["length_scale_m"] = iodata.units.GetScaleFactor<Units::ValueType::LENGTH>();
  const auto &probes = iodata.domains.postpro.probe;
  Require(!probes.empty(), "No probes in input");
  const int count = static_cast<int>(probes.size());
  mfem::DenseMatrix points(3, count);
  std::vector<int> ids;
  report["probes"] = json::array();
  int i = 0;
  for (const auto &[id, data] : probes)
  {
    ids.push_back(id);
    for (int d = 0; d < 3; d++)
    {
      points(d, i) = data.center[d];
      Require(std::isfinite(points(d, i)), "Non-finite normalized probe coordinate");
    }
    report["probes"].push_back(
        {{"id", id},
         {"configured_center_model_units", original_probes.at(id).center},
         {"normalized_center", data.center},
         {"physical_center_m",
          iodata.units.Dimensionalize<Units::ValueType::LENGTH>(data.center)}});
    i++;
  }
  report["probe_count"] = count;
  report["inverse_parameters"] = {{"reference_tolerance", 1.0e-15},
                                  {"physical_relative_tolerance", 4.0e-15},
                                  {"element_tolerance", 1.0e-8},
                                  {"max_iterations", 16},
                                  {"solver", "NewtonElementProject"},
                                  {"initial_guess_grid", "OpenHalfUniform"},
                                  {"initial_guess_relative_order", -1},
                                  {"strict_interior_margin", 1.0e-7},
                                  {"forward_residual_relative_limit", 1.0e-12}};
  using Inverse = mfem::InverseElementTransformation;
  report["attempts"] = json::array();
  report["attempts"].push_back(Locate(mesh, points, ids, "Center", Inverse::Center));
  report["attempts"].push_back(
      Locate(mesh, points, ids, "ClosestPhysNode", Inverse::ClosestPhysNode));
  report["attempts"].push_back(
      Locate(mesh, points, ids, "ClosestRefNode", Inverse::ClosestRefNode));
  report["newly_found_vs_center"] = json::array();
  report["unresolved_all_modes"] = json::array();
  for (int j = 0; j < count; j++)
  {
    const bool center = report["attempts"][0]["points"][j]["element"].get<int>() >= 0;
    const bool physical = report["attempts"][1]["points"][j]["element"].get<int>() >= 0;
    const bool reference = report["attempts"][2]["points"][j]["element"].get<int>() >= 0;
    if (!center && (physical || reference))
    {
      report["newly_found_vs_center"].push_back(ids[j]);
    }
    if (!center && !physical && !reference)
    {
      report["unresolved_all_modes"].push_back(ids[j]);
    }
  }
  report["bounded_candidate_search"] =
      BroadenCandidates(mesh, points, ids, report["attempts"][0]);
  report["interpretation_scope"] =
      "Rescued Center misses implicate Newton initialization within the same candidate "
      "neighborhood; all-mode misses alone cannot distinguish a neighborhood miss from "
      "inverse failure. Bounded candidate rescue with the same Center inverse and an "
      "element "
      "outside the original vertex neighborhood proves a candidate-selection limitation "
      "on a conforming mesh. Exhausting K candidates does not prove a point is outside. "
      "No GSLIB oracle or field interpolation performed.";
  report["total"] = total.Elapsed();
  report["complete"] = true;
  std::ofstream output(report_path);
  Require(bool(output), "Cannot create diagnostic report");
  output << report.dump(2) << '\n';
  Require(bool(output), "Failed to write diagnostic report");
  std::fprintf(stderr,
               "PALACE_LOCATOR_DIAGNOSTIC complete=1 probes=%d solve=0 gslib=0 rf=0\n",
               count);
}
}  // namespace

int main(int argc, char *argv[])
{
  using namespace palace;
  if (argc != 4)
  {
    std::fprintf(stderr, "Usage: %s CONFIG REPORT HOST-VERIFIED-IDENTITY.json\n", argv[0]);
    return 2;
  }
  Mpi::Init(argc, argv);
  int result = 0;
  {
    const int threads = utils::ConfigureOmp();
    mfem::Device device("cpu,omp");
    hypre::Initialize();
    ceed::Initialize("/cpu/self", "/opt/palace-cudss/include/palace/");
    try
    {
      Run(argv[1], argv[2], argv[3], threads);
    }
    catch (const std::exception &error)
    {
      std::fprintf(stderr, "PALACE_LOCATOR_DIAGNOSTIC failed: %s\n", error.what());
      result = 1;
    }
    ceed::Finalize();
  }
  Mpi::Finalize();
  return result;
}
