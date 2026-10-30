// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Synthetic CUDA field replay, never a Maxwell solve or an RF qualification.
// Usage: stage-probe-gpu-field CONFIG REPORT HOST-VERIFIED-IDENTITY.json
#if !defined(__CUDACC__)
#error "Compile this replay with the cached native CUDA compiler/SM120 flags"
#endif
#include <algorithm>
#include <chrono>
#include <cmath>
#include <complex>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <vector>
#include <cuda_runtime.h>
#include <mfem.hpp>
#include <nlohmann/json.hpp>
#include <mfem/general/forall.hpp>
#if !defined(MFEM_USE_CUDA)
#error "The pinned MFEM must have CUDA support"
#endif
#include "drivers/drivensolver.hpp"
#include "fem/gridfunction.hpp"
#include "fem/interpolator.hpp"
#include "fem/libceed/ceed.hpp"
#include "fem/mesh.hpp"
#include "linalg/hypre.hpp"
#include "models/spaceoperator.hpp"
#include "utils/communication.hpp"
#include "utils/geodata.hpp"
#include "utils/iodata.hpp"
#include "utils/omp.hpp"
#include "utils/outputdir.hpp"

namespace
{
using json = nlohmann::json;
using Clock = std::chrono::steady_clock;
constexpr double RelativeL2Limit = 1.0e-9;
constexpr double ScaledMaxAbsLimit = 1.0e-8;
constexpr double PhaseFloorRelative = 1.0e-6;

void Require(bool condition, const char *message)
{
  if (!condition)
  {
    throw std::runtime_error(message);
  }
}
void CUDA(cudaError_t status)
{
  if (status != cudaSuccess)
  {
    throw std::runtime_error(cudaGetErrorString(status));
  }
}
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

MFEM_HOST_DEVICE inline double Pattern(int index, unsigned seed, unsigned component)
{
  const auto bits =
      (static_cast<unsigned>(index) * 1664525u + seed + 97u * component) & 1023u;
  return (static_cast<int>(bits) - 512) * 0x1p-10;  // Exactly representable FP64 DOFs.
}
MFEM_HOST_DEVICE inline int WriterArchitecture()
{
#if defined(__CUDA_ARCH__)
  return __CUDA_ARCH__;
#else
  return 0;  // A CPU-dispatched forall must fail the witness check.
#endif
}

json FillDevice(palace::GridFunction &field, unsigned seed)
{
  Require(mfem::Device::Allows(mfem::Backend::CUDA_MASK), "CUDA dispatch is not enabled");
  Require(field.HasImag() && field.Real().Size() > 0, "Expected complex nonempty field");
  field.Real().UseDevice(true);
  field.Imag().UseDevice(true);
  auto *real = field.Real().Write();
  auto *imag = field.Imag().Write();
  cudaPointerAttributes real_attributes{}, imag_attributes{};
  CUDA(cudaPointerGetAttributes(&real_attributes, real));
  CUDA(cudaPointerGetAttributes(&imag_attributes, imag));
  Require(real_attributes.type == cudaMemoryTypeManaged &&
              imag_attributes.type == cudaMemoryTypeManaged,
          "Replay requires actual managed CUDA field pointers (adapter policy)");
  int *witness = nullptr;
  CUDA(cudaMalloc(reinterpret_cast<void **>(&witness), sizeof(int)));
  const int size = field.Real().Size();
  const TimePoint start;
  mfem::forall(size,
               [=] MFEM_HOST_DEVICE(int i)
               {
                 real[i] = Pattern(i, seed, 0);
                 imag[i] = Pattern(i, seed, 1);
                 if (i == 0)
                 {
                   *witness = WriterArchitecture();
                 }
               });
  CUDA(cudaGetLastError());
  CUDA(cudaDeviceSynchronize());
  json report = start.Elapsed();
  int actual_architecture = 0;
  CUDA(cudaMemcpy(&actual_architecture, witness, sizeof(int), cudaMemcpyDeviceToHost));
  CUDA(cudaFree(witness));
  Require(actual_architecture > 0, "Field write used CPU instead of the CUDA kernel");
  report["cuda_writer_architecture"] = actual_architecture;
  report["real_pointer_memory_type"] = static_cast<int>(real_attributes.type);
  report["imag_pointer_memory_type"] = static_cast<int>(imag_attributes.type);
  report["managed_pointer_proof"] = true;
  report["dofs_per_component"] = size;
  report["seed"] = seed;
  return report;
}

json FirstHostRead(palace::GridFunction &field, unsigned seed)
{
  const TimePoint total;
  const TimePoint read_start;
  const auto *real = field.Real().HostRead();
  const auto *imag = field.Imag().HostRead();
  CUDA(cudaDeviceSynchronize());
  json result = {{"host_read_calls", read_start.Elapsed()}};
  const TimePoint verification;
  const int count = std::min(128, field.Real().Size());
  for (int j = 0; j < count; j++)
  {
    const int index = count == 1
                          ? 0
                          : static_cast<int>(static_cast<long long>(j) *
                                             (field.Real().Size() - 1) / (count - 1));
    Require(real[index] == Pattern(index, seed, 0) &&
                imag[index] == Pattern(index, seed, 1),
            "Strided host samples do not match exact GPU-written DOF pattern");
  }
  result["strided_verification"] = verification.Elapsed();
  result["strided_samples_per_component"] = count;
  result["exact_equality_pass"] = true;
  result["total_host_read_plus_samples"] = total.Elapsed();
  result["scope"] = "API copy plus 128 strided reads; not a physical UVM migration counter";
  return result;
}

json Compare(const std::vector<std::complex<double>> &actual,
             const std::vector<std::complex<double>> &reference)
{
  Require(actual.size() == reference.size(), "Probe vector layout/size mismatch");
  long double difference_squared = 0.0L, reference_squared = 0.0L;
  double max_error = 0.0, reference_max = 0.0;
  bool finite = true;
  for (std::size_t i = 0; i < reference.size(); i++)
  {
    finite = finite && std::isfinite(actual[i].real()) && std::isfinite(actual[i].imag()) &&
             std::isfinite(reference[i].real()) && std::isfinite(reference[i].imag());
    const double difference = std::abs(actual[i] - reference[i]);
    difference_squared += static_cast<long double>(difference) * difference;
    const double amplitude = std::abs(reference[i]);
    reference_squared += static_cast<long double>(amplitude) * amplitude;
    max_error = std::max(max_error, difference);
    reference_max = std::max(reference_max, amplitude);
  }
  const double relative =
      reference_squared > 0.0L
          ? static_cast<double>(std::sqrt(difference_squared / reference_squared))
          : 0.0;
  const bool relative_pass =
      reference_squared > 0.0L ? relative <= RelativeL2Limit : difference_squared == 0.0L;
  const double absolute_limit = ScaledMaxAbsLimit * std::max(1.0, reference_max);
  const double phase_floor = PhaseFloorRelative * std::max(1.0, reference_max);
  int phase_samples = 0;
  double max_phase_error = 0.0;
  json values = json::array();
  for (std::size_t i = 0; i < reference.size(); i++)
  {
    const bool phase_mask =
        std::abs(reference[i]) > phase_floor && std::abs(actual[i]) > phase_floor;
    double phase_error = 0.0;
    if (phase_mask)
    {
      phase_error = std::abs(std::arg(actual[i] * std::conj(reference[i])));
      max_phase_error = std::max(max_phase_error, phase_error);
      phase_samples++;
    }
    values.push_back({{"flat_index", i},
                      {"native", {actual[i].real(), actual[i].imag()}},
                      {"oracle", {reference[i].real(), reference[i].imag()}},
                      {"phase_mask", phase_mask},
                      {"phase_error_rad", phase_mask ? json(phase_error) : json(nullptr)}});
  }
  return {
      {"passed", finite && relative_pass && max_error <= absolute_limit},
      {"all_finite", finite},
      {"complex_relative_l2", reference_squared > 0.0L ? json(relative) : json(nullptr)},
      {"relative_l2_pass", relative_pass},
      {"max_abs_error", max_error},
      {"reference_max_amplitude", reference_max},
      {"max_abs_error_limit", absolute_limit},
      {"phase_amplitude_floor", phase_floor},
      {"phase_samples", phase_samples},
      {"phase_excluded_samples", reference.size() - phase_samples},
      {"max_phase_error_rad_above_floor",
       phase_samples ? json(max_phase_error) : json(nullptr)},
      {"phase_scope",
       "Diagnostic above declared amplitude floor; no fabricated near-zero phase"},
      {"values", values}};
}

json Replay(palace::GridFunction &field, unsigned seed,
            palace::InterpolationOperator &candidate, palace::InterpolationOperator &oracle,
            int probes)
{
  json result;
  result["initial_device_fill"] = FillDevice(field, seed);
  result["explicit_first_host_read"] = FirstHostRead(field, seed);
  // Refill on the device before EACH backend so warm CPU pages cannot hide the first
  // backend's HostRead in the second backend's timing.
  result["refill_before_native"] = FillDevice(field, seed);
  TimePoint sampling;
  const auto actual = candidate.ProbeField(field);
  CUDA(cudaDeviceSynchronize());
  result["native_sampling"] = sampling.Elapsed();
  Require(candidate.UsesMFEMLocator(), "Native probe backend unexpectedly fell back");
  result["refill_before_oracle"] = FillDevice(field, seed);
  sampling = TimePoint{};
  const auto reference = oracle.ProbeField(field);
  CUDA(cudaDeviceSynchronize());
  result["oracle_sampling"] = sampling.Elapsed();
  Require(field.VectorDim() == 3 && actual.size() == static_cast<std::size_t>(3 * probes),
          "Expected all probes with point-major three-vector components");
  result["field_components"] = field.VectorDim();
  result["fes_ordering_enum"] = static_cast<int>(field.FESpace()->GetOrdering());
  result["comparison"] = Compare(actual, reference);
  return result;
}

void Run(const char *config_path, const char *report_path, const char *identity_path,
         int threads)
{
  using namespace palace;
  static_assert(sizeof(mfem::real_t) == 8, "Synthetic field replay requires FP64 MFEM");
  MPI_Comm comm = Mpi::World();
  Require(Mpi::Size(comm) == 1 && threads == 1, "Replay requires rank1/OMP1");
  Require(mfem::Device::Allows(mfem::Backend::CUDA_MASK), "Replay requires CUDA");
  Require(!fs::exists(report_path), "Do not overwrite a previous replay report");
  const char *managed = std::getenv("PALACE_CUDA_MANAGED");
  Require(managed && std::strcmp(managed, "1") == 0,
          "Managed-memory adapter policy required");
  std::ifstream identity_file(identity_path);
  Require(bool(identity_file), "Cannot open host-verified input identity");
  json report = {{"schema", 1},
                 {"synthetic_gpu_field_replay", true},
                 {"rf_result", false},
                 {"solve_executed", false},
                 {"config_path", config_path},
                 {"provided_input_identity", json::parse(identity_file)},
                 {"identity_scope", "Host must independently verify hashes before/after"},
                 {"relative_l2_limit", RelativeL2Limit},
                 {"max_abs_scaled_limit", ScaledMaxAbsLimit},
                 {"phase_floor_relative", PhaseFloorRelative}};
  cudaDeviceProp properties{};
  CUDA(cudaGetDeviceProperties(&properties, 0));
  report["cuda_device"] = {{"name", properties.name},
                           {"major", properties.major},
                           {"minor", properties.minor},
                           {"memory_bytes", properties.totalGlobalMem}};
  report["pattern"] = "(((uint32(index)*1664525 + seed + 97*component) & 1023)-512)*2^-10";
  report["storage_bytes_per_dof"] = sizeof(mfem::real_t);
  const TimePoint total;
  IoData iodata(config_path, false);
  Require(iodata.problem.type == ProblemType::DRIVEN &&
              iodata.model.refinement.max_it == 0 &&
              iodata.solver.driven.adaptive_tol <= 0.0,
          "Replay requires original driven fixed-mesh input");
  Require(!fs::exists(iodata.problem.output), "Use fresh Problem.Output");
  MakeOutputFolder(iodata, comm);
  DrivenSolver solver(iodata, true, 1, threads, nullptr);
  TimePoint phase;
  auto serial_mesh = mesh::Load(iodata, comm);
  solver.Preprocess(iodata, serial_mesh, comm);
  std::vector<std::unique_ptr<mfem::ParMesh>> levels;
  levels.push_back(mesh::Partition(iodata, std::move(serial_mesh), comm));
  mesh::RefineMesh(iodata, levels);
  std::vector<std::unique_ptr<Mesh>> meshes;
  for (auto &level : levels)
  {
    meshes.push_back(std::make_unique<Mesh>(std::move(level)));
  }
  report["preprocessing"] = phase.Elapsed();
  auto &mesh = meshes.back()->Get();
  const auto sequence = mesh.GetSequence(), nodes_sequence = mesh.GetNodesSequence();
  report["mesh"] = {{"elements", mesh.GetNE()},
                    {"vertices", mesh.GetNV()},
                    {"boundary_elements", mesh.GetNBE()},
                    {"curvature_order", mesh.GetNodes()->FESpace()->GetMaxElementOrder()}};
  phase = TimePoint{};
  SpaceOperator space(iodata, meshes);  // FE spaces/materials only: no K/C/M or KSP call.
  report["space_operator"] = phase.Elapsed();
  setenv("PALACE_PROBE_LOCATOR", "mfem", 1);
  phase = TimePoint{};
  InterpolationOperator candidate(iodata, space.GetNDSpace());
  report["native_locator_constructor"] = phase.Elapsed();
  Require(candidate.UsesMFEMLocator(), "Actual native geometry locator selected fallback");
  setenv("PALACE_PROBE_LOCATOR", "gslib", 1);
  phase = TimePoint{};
  InterpolationOperator oracle(iodata, space.GetNDSpace());  // Exactly one GSLIB setup.
  report["oracle_locator_constructor"] = phase.Elapsed();
  const int probes = static_cast<int>(candidate.GetProbes().size());
  Require(candidate.GetProbes() == oracle.GetProbes(), "Probe ID ordering differs");
  report["probe_ids"] = candidate.GetProbes();
  report["probe_count"] = probes;
  report["length_scale_m"] = iodata.units.GetScaleFactor<Units::ValueType::LENGTH>();
  report["normalized_centers"] = json::array();
  for (const auto &[id, data] : iodata.domains.postpro.probe)
  {
    report["normalized_centers"].push_back({{"id", id}, {"center", data.center}});
  }
  GridFunction electric(space.GetNDSpace(), true);
  report["E_ND"] = Replay(electric, 17u, candidate, oracle, probes);
  GridFunction magnetic(space.GetRTSpace(), true);
  report["B_RT"] = Replay(magnetic, 103u, candidate, oracle, probes);
  Require(sequence == mesh.GetSequence() && nodes_sequence == mesh.GetNodesSequence(),
          "Mesh revision changed during synthetic replay");
  report["complete"] = true;
  report["passed"] = report["E_ND"]["comparison"]["passed"].get<bool>() &&
                     report["B_RT"]["comparison"]["passed"].get<bool>();
  report["total"] = total.Elapsed();
  std::ofstream output(report_path);
  Require(bool(output), "Cannot create replay report");
  output << report.dump(2) << '\n';
  Require(bool(output), "Failed to write replay report");
  Require(report["passed"].get<bool>(),
          "GPU field replay exceeded predeclared accuracy gates");
  std::fprintf(stderr, "PALACE_GPU_FIELD_REPLAY complete=1 probes=%d gpu_writes=1 rf=0\n",
               probes);
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
    mfem::Device device("cuda,omp", 0);
    hypre::Initialize();
    ceed::Initialize("/gpu/cuda/magma", "/opt/palace-cudss/include/palace/");
    try
    {
      Run(argv[1], argv[2], argv[3], threads);
    }
    catch (const std::exception &error)
    {
      std::fprintf(stderr, "PALACE_GPU_FIELD_REPLAY failed: %s\n", error.what());
      result = 1;
    }
    ceed::Finalize();
  }
  Mpi::Finalize();
  return result;
}
