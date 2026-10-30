// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include "driver.hpp"

#include <memory>
#include <vector>
#include <mfem.hpp>
#include <nlohmann/json.hpp>
#include "drivers/basesolver.hpp"
#include "drivers/boundarymodesolver.hpp"
#include "drivers/drivensolver.hpp"
#include "drivers/eigensolver.hpp"
#include "drivers/electrostaticsolver.hpp"
#include "drivers/magnetostaticsolver.hpp"
#include "drivers/transientsolver.hpp"
#include "fem/mesh.hpp"
#include "utils/communication.hpp"
#include "utils/configfile.hpp"
#include "utils/geodata.hpp"
#include "utils/iodata.hpp"
#include "utils/memoryreporting.hpp"
#include "utils/outputdir.hpp"
#include "utils/stageprobe.hpp"
#include "utils/stageprofile.hpp"
#include "utils/timer.hpp"

namespace palace
{

void Run(IoData &iodata, MPI_Comm comm, int omp_threads, const char *git_tag)
{
  const bool world_root = Mpi::Root(comm);
  const int world_size = Mpi::Size(comm);
  const auto stage_probe = RequestedStageProbe();
  if (stage_probe != StageProbe::None)
  {
    MFEM_VERIFY(world_size == 1, "Stage diagnostics require exactly one MPI rank!");
    if (stage_probe == StageProbe::Operators)
    {
      MFEM_VERIFY(iodata.problem.type == ProblemType::DRIVEN &&
                      iodata.solver.driven.adaptive_tol <= 0.0 &&
                      iodata.model.refinement.max_it == 0,
                  "Operator diagnostics require a driven uniform fixed-mesh solve!");
    }
  }

  std::unique_ptr<BaseSolver> solver = [&]() -> std::unique_ptr<BaseSolver>
  {
    switch (iodata.problem.type)
    {
      case ProblemType::DRIVEN:
        return std::make_unique<DrivenSolver>(iodata, world_root, world_size, omp_threads,
                                              git_tag);
      case ProblemType::EIGENMODE:
        return std::make_unique<EigenSolver>(iodata, world_root, world_size, omp_threads,
                                             git_tag);
      case ProblemType::ELECTROSTATIC:
        return std::make_unique<ElectrostaticSolver>(iodata, world_root, world_size,
                                                     omp_threads, git_tag);
      case ProblemType::MAGNETOSTATIC:
        return std::make_unique<MagnetostaticSolver>(iodata, world_root, world_size,
                                                     omp_threads, git_tag);
      case ProblemType::TRANSIENT:
        return std::make_unique<TransientSolver>(iodata, world_root, world_size,
                                                 omp_threads, git_tag);
      case ProblemType::BOUNDARYMODE:
        return std::make_unique<BoundaryModeSolver>(iodata, world_root, world_size,
                                                    omp_threads, git_tag);
    }
    return nullptr;
  }();
  MFEM_VERIFY(solver, "Unknown problem type in palace::Run!");

  std::vector<std::unique_ptr<Mesh>> mesh;
  {
    // Mesh loading/partitioning/refinement is part of initialization: opening
    // an INIT BlockTimer here (with the stack otherwise empty) credits the
    // umbrella time to "Initialization" and nests the inner MESH_PREPROCESS
    // timers under it, matching the "  Mesh Preprocessing" row's indentation.
    BlockTimer bt(Timer::INIT);
    auto smesh = mesh::Load(iodata, comm);
    {
      StageProfile profile("preprocess.units");
      solver->Preprocess(iodata, smesh, comm);
    }
    std::vector<std::unique_ptr<mfem::ParMesh>> mfem_mesh;
    mfem_mesh.push_back(mesh::Partition(iodata, std::move(smesh), comm));
    mesh::RefineMesh(iodata, mfem_mesh);
    Mpi::Print(comm, "\n");
    memory_reporting::PrintMemoryUsage(comm, memory_reporting::GetCurrentMemoryStats(comm));
    memory_reporting::PrintMemoryUsage(comm,
                                       memory_reporting::GetCurrentNodeMemoryStats(comm));
    {
      StageProfile profile("preprocess.mesh_wrappers");
      for (auto &m : mfem_mesh)
      {
        mesh.push_back(std::make_unique<Mesh>(std::move(m)));
      }
    }
  }

  bool stage_complete = (stage_probe == StageProbe::Preprocess);
  if (!stage_complete)
  {
    try
    {
      solver->SolveEstimateMarkRefine(mesh);
    }
    catch (const StageProbeComplete &complete)
    {
      MFEM_VERIFY(stage_probe == StageProbe::Operators &&
                      complete.stage == StageProbe::Operators,
                  "Unexpected diagnostic completion stage!");
      stage_complete = true;
    }
  }
  if (stage_probe != StageProbe::None)
  {
    MFEM_VERIFY(stage_complete, "Requested diagnostic stage did not complete!");
    const char *stage = stage_probe == StageProbe::Preprocess ? "preprocess" : "operators";
    WriteRootOutputFile(
        fs::path(iodata.problem.output) / "stage-diagnostic.json", comm,
        [&](auto &stream)
        {
          nlohmann::json levels = nlohmann::json::array();
          for (const auto &m : mesh)
          {
            const auto &pm = m->Get();
            levels.push_back(
                {{"elements", pm.GetNE()},
                 {"boundary_elements", pm.GetNBE()},
                 {"vertices", pm.GetNV()},
                 {"attributes",
                  std::vector<int>(pm.attributes.begin(), pm.attributes.end())},
                 {"boundary_attributes",
                  std::vector<int>(pm.bdr_attributes.begin(), pm.bdr_attributes.end())}});
          }
          nlohmann::json diagnostic = {{"schema", 1},
                                       {"stage", stage},
                                       {"diagnostic_only", true},
                                       {"complete", true},
                                       {"solve_executed", false},
                                       {"rf_result", false},
                                       {"mpi_ranks", world_size},
                                       {"mesh_levels", levels}};
          stream << diagnostic.dump(2) << '\n';
        });
  }

  auto peak_mem = memory_reporting::GetPeakMemoryStats(comm);
  auto peak_node_mem = memory_reporting::GetPeakNodeMemoryStats(comm);
  Mpi::Print(comm, "\n");
  memory_reporting::PrintMemoryUsage(comm, peak_mem);
  memory_reporting::PrintMemoryUsage(comm, peak_node_mem);
  BlockTimer::Finalize(comm);
  BlockTimer::Print(comm);
  solver->SaveMetadata(BlockTimer::GlobalTimer());
  solver->SaveMetadata(peak_mem);
  solver->SaveMetadata(peak_node_mem);
  if (stage_probe != StageProbe::None)
  {
    Mpi::Print(comm,
               "PALACE_STAGE_DIAGNOSTIC: stage={} complete=1 solve_executed=0 "
               "rf_result=0\n",
               stage_probe == StageProbe::Preprocess ? "preprocess" : "operators");
  }
  Mpi::Print(comm, "\n");
}

}  // namespace palace
