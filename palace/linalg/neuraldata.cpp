// SPDX-License-Identifier: Apache-2.0

#include "neuraldata.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <numbers>
#include <stdexcept>
#include <mfem.hpp>
#include <nlohmann/json.hpp>
#include "fem/fespace.hpp"
#include "linalg/complexcsr.hpp"
#include "linalg/rap.hpp"
#include "utils/communication.hpp"

namespace palace
{

namespace
{

void RequireNeuralProbeSpace(const FiniteElementSpace &space)
{
  const int n = space.GetTrueVSize();
  if (Mpi::Size(space.GetComm()) != 1 || space.IsBroken() ||
      !space.GetParMesh().Conforming() || space.SpaceDimension() != 3 ||
      space.GetMaxElementOrder() != 1 ||
      !dynamic_cast<const mfem::ND_FECollection *>(&space.GetFEColl()) || n <= 0 ||
      n != space.GlobalTrueVSize())
  {
    throw std::invalid_argument(
        "Neural probes require conforming single-rank ND1 true DOFs");
  }
}

}  // namespace

NeuralProbeFields ProjectNeuralProbeFields(FiniteElementSpace &space,
                                           std::span<const int> essential_tdofs)
{
  constexpr int width = 8;
  RequireNeuralProbeSpace(space);
  const int n = space.GetTrueVSize();
  if (std::any_of(essential_tdofs.begin(), essential_tdofs.end(),
                  [=](int i) { return i < 0 || i >= n; }))
  {
    throw std::invalid_argument("Neural probe essential true DOFs are out of range");
  }

  mfem::Vector lo, hi;
  space.GetParMesh().GetBoundingBox(lo, hi);
  mfem::Vector center(hi);
  center += lo;
  center *= 0.5;
  hi -= lo;
  const double length = hi.Max();
  if (!std::isfinite(length) || length <= 0.0)
  {
    throw std::invalid_argument(
        "Neural probes require a finite positive bounding-box extent");
  }

  const auto size = static_cast<std::size_t>(n) * width;
  NeuralProbeFields result{std::vector<double>(size), std::vector<double>(size), length};
  mfem::ParGridFunction projected(&space.Get());
  mfem::Vector true_dofs(n);
  for (int j = 0; j < width; ++j)
  {
    mfem::VectorFunctionCoefficient field(3,
                                          [&, j](const mfem::Vector &x, mfem::Vector &y)
                                          {
                                            const double a = (x[0] - center[0]) / length;
                                            const double b = (x[1] - center[1]) / length;
                                            const double c = (x[2] - center[2]) / length;
                                            y = 0.0;
                                            switch (j)
                                            {
                                              case 0:
                                                y[0] = 1.0;
                                                break;
                                              case 1:
                                                y[1] = 1.0;
                                                break;
                                              case 2:
                                                y[2] = 1.0;
                                                break;
                                              case 3:
                                                y[1] = a;
                                                break;
                                              case 4:
                                                y[2] = b;
                                                break;
                                              case 5:
                                                y[0] = c;
                                                break;
                                              case 6:
                                                y[2] = std::sin(std::numbers::pi * a);
                                                break;
                                              case 7:
                                                y[0] = std::sin(std::numbers::pi * b);
                                                break;
                                            }
                                            y /= length;
                                          });
    projected.ProjectCoefficient(field);
    projected.GetTrueDofs(true_dofs);
    auto *values = true_dofs.HostReadWrite();
    for (int i : essential_tdofs)
    {
      values[i] = 0.0;
    }

    for (int i = 0; i < n; ++i)
    {
      result.real[static_cast<std::size_t>(i) * width + j] = values[i];
    }
  }
  return result;
}

namespace
{

using Json = nlohmann::json;

bool IsHexDigest(const std::string &value, std::size_t length)
{
  return value.size() == length &&
         value.find_first_not_of("0123456789abcdef") == std::string::npos;
}

std::size_t StoredEntries(const Operator *op)
{
  if (!op)
  {
    return 0;
  }
  if (const auto *matrix = dynamic_cast<const mfem::HypreParMatrix *>(op))
  {
    return matrix->NNZ();
  }
  if (const auto *part = dynamic_cast<const ParOperator *>(op))
  {
    return part->ParallelAssemble().NNZ();
  }
  throw std::invalid_argument("Neural capture requires assembled Hypre operator parts");
}

Json ProbeRows(const std::vector<double> &values)
{
  constexpr std::size_t width = 8;
  Json rows = Json::array();
  for (auto it = values.begin(); it != values.end(); it += width)
  {
    if (!std::all_of(it, it + width, [](double x) { return std::isfinite(x); }))
    {
      throw std::invalid_argument("Nonfinite neural probe");
    }
    rows.push_back(std::vector<double>(it, it + width));
  }
  return rows;
}

struct StagingDirectory
{
  std::filesystem::path path;
  explicit StagingDirectory(std::filesystem::path path) : path(std::move(path))
  {
    if (!std::filesystem::create_directory(this->path))
    {
      throw std::runtime_error("Neural capture staging directory already exists");
    }
  }
  ~StagingDirectory()
  {
    std::error_code error;
    std::filesystem::remove(path / "capture.json", error);
    std::filesystem::remove(path, error);
  }
};

}  // namespace

struct NeuralCapture::Data
{
  Json payload;
  std::vector<int> essential;
  NeuralCaptureLimits limits;
  int n;
};

NeuralCapture::NeuralCapture(const ComplexParOperator &bc, FiniteElementSpace &coarse_space,
                             const NeuralCaptureMetadata &metadata,
                             const NeuralCaptureLimits &limits)
{
  constexpr std::size_t max_capture_bytes = 64 * 1024 * 1024;
  constexpr std::size_t capture_overhead = 4096;
  const int n = bc.Height();
  if (limits.max_rows <= 0 || !limits.max_nnz || limits.max_bytes > max_capture_bytes ||
      !limits.max_samples || limits.max_samples > 8 || n <= 0 || bc.Width() != n ||
      (!bc.Real() && !bc.Imag()) || &bc.TrialFiniteElementSpace() != &coarse_space ||
      &bc.TestFiniteElementSpace() != &coarse_space || Mpi::Size(bc.GetComm()) != 1 ||
      metadata.geometry_id.empty() || metadata.geometry_id.size() > 128 ||
      metadata.geometry_id.find_first_not_of(
          "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
          ".") != std::string::npos ||
      !IsHexDigest(metadata.mesh_sha256, 64) || !IsHexDigest(metadata.source_sha, 40) ||
      !IsHexDigest(metadata.config_sha256, 64) || !std::isfinite(metadata.omega) ||
      metadata.omega <= 0)
  {
    throw std::invalid_argument("Invalid neural capture scope, identity or limits");
  }
  RequireNeuralProbeSpace(coarse_space);
  if (n > limits.max_rows)
  {
    throw NeuralCaptureBudgetExceeded("row_limit");
  }
  if (limits.max_bytes < capture_overhead)
  {
    throw NeuralCaptureBudgetExceeded("byte_limit");
  }

  // Bound JSON before allocating CSR copies, projected fields and sample
  // storage. The two parts may share columns. Their sum still bounds the merged
  // CSR.
  const std::size_t real_nnz = StoredEntries(bc.Real());
  const std::size_t imag_nnz = StoredEntries(bc.Imag());
  const auto row_bytes = std::size_t(640) + 64 * limits.max_samples;
  const auto bytes = limits.max_bytes - capture_overhead;
  if (real_nnz > limits.max_nnz || imag_nnz > limits.max_nnz - real_nnz)
  {
    throw NeuralCaptureBudgetExceeded("nnz_limit");
  }
  if (static_cast<std::size_t>(n) > bytes / row_bytes || real_nnz > bytes / 96 ||
      imag_nnz > bytes / 96 - real_nnz ||
      real_nnz + imag_nnz > (bytes - n * row_bytes) / 96)
  {
    throw NeuralCaptureBudgetExceeded("byte_limit");
  }

  std::vector<int> essential;
  if (const auto *mask = bc.GetEssentialTrueDofs())
  {
    essential.assign(mask->begin(), mask->end());
    std::sort(essential.begin(), essential.end());
    if (std::adjacent_find(essential.begin(), essential.end()) != essential.end() ||
        essential.size() >= static_cast<std::size_t>(n))
    {
      throw std::invalid_argument("Invalid neural capture essential true DOFs");
    }
  }
  auto phi = ProjectNeuralProbeFields(coarse_space, essential);
  const double context = metadata.omega * phi.bbox_length;
  if (!std::isfinite(context) || context <= 0)
  {
    throw std::invalid_argument("Invalid neural capture frequency context");
  }

  const ComplexLocalCSR csr(bc, false);
  if (csr.first_row != 0 || csr.n_glob != n || csr.n_loc != n || csr.V.empty() ||
      csr.V.size() > real_nnz + imag_nnz)
  {
    throw std::invalid_argument("Invalid neural capture CSR distribution");
  }
  std::vector<double> vr, vi;
  vr.reserve(csr.V.size());
  vi.reserve(csr.V.size());
  for (const auto &v : csr.V)
  {
    if (!std::isfinite(v.real()) || !std::isfinite(v.imag()))
    {
      throw std::invalid_argument("Nonfinite neural capture CSR value");
    }
    vr.push_back(v.real());
    vi.push_back(v.imag());
  }

  Json payload = {
      {"schema", "palace-neural-capture"},
      {"version", 1},
      {"scope",
       {{"problem", "driven_uniform"},
        {"mpi_ranks", 1},
        {"coarse_space", "conforming_nd"},
        {"coarse_order", 1}}},
      {"geometry_id", metadata.geometry_id},
      {"mesh_sha256", metadata.mesh_sha256},
      {"source_sha", metadata.source_sha},
      {"config_sha256", metadata.config_sha256},
      {"operator_kind", "complex_level_0_preconditioner"},
      {"n_local", n},
      {"n_global", csr.n_glob},
      {"first_row", csr.first_row},
      {"coarse_order", 1},
      {"indptr", csr.I},
      {"indices", csr.J},
      {"values_real", std::move(vr)},
      {"values_imag", std::move(vi)},
      {"essential_true_dofs", essential},
      {"normalization_version", "scalar-row-l1-v1"},
      {"phi_version", "phi-global-nd-v1"},
      {"phi", {{"real", ProbeRows(phi.real)}, {"imag", ProbeRows(phi.imag)}}},
      {"context", {context, int(metadata.pc_mat_shifted), int(metadata.pc_mat_real)}},
      {"samples", Json::array()}};
  data = std::make_unique<Data>(Data{std::move(payload), std::move(essential), limits, n});
}

NeuralCapture::~NeuralCapture() = default;

bool NeuralCapture::AppendRhs(const ComplexVector &rhs, int excitation_id)
{
  auto &samples = data->payload["samples"];
  if (samples.size() == data->limits.max_samples)
  {
    return false;
  }
  if (rhs.Size() != data->n || excitation_id < 0)
  {
    throw std::invalid_argument("Invalid neural capture RHS size or excitation");
  }
  const auto *re = rhs.Real().HostRead();
  const auto *im = rhs.Imag().HostRead();
  double norm = 0;
  for (int i = 0; i < data->n; ++i)
  {
    norm = std::hypot(norm, std::hypot(re[i], im[i]));
  }
  if (!std::isfinite(norm) ||
      std::any_of(data->essential.begin(), data->essential.end(),
                  [&](int i) { return re[i] != 0.0 || im[i] != 0.0; }))
  {
    throw std::invalid_argument("Nonfinite neural capture RHS or nonzero essential entry");
  }
  samples.push_back({{"source_kind", "observed_coarse_rhs"},
                     {"outer_rhs_or_port_id", excitation_id},
                     {"coarse_application_index", samples.size() + 1},
                     {"r",
                      {{"real", std::vector<double>(re, re + data->n)},
                       {"imag", std::vector<double>(im, im + data->n)}}},
                     {"reference_status", "unlabeled"},
                     {"reference_source", nullptr},
                     {"reference_actual_residual_abs", nullptr},
                     {"reference_tolerance", nullptr},
                     {"reference_rhs_norm", norm}});
  return true;
}

std::size_t NeuralCapture::Write(const std::filesystem::path &path) const
{
  if (path.filename().empty() || data->payload["samples"].empty())
  {
    throw std::invalid_argument("Neural capture requires a destination and samples");
  }
  auto staging_path = path;
  staging_path += ".tmp";
  StagingDirectory staging(staging_path);
  const auto temp = staging.path / "capture.json";
  std::ofstream file(temp, std::ios::binary);
  file.exceptions(std::ios::badbit | std::ios::failbit);
  file << data->payload << '\n';
  file.close();
  const auto size = std::filesystem::file_size(temp);
  if (size > data->limits.max_bytes)
  {
    throw NeuralCaptureBudgetExceeded("byte_limit");
  }
  // Publish atomically; an existing capture is never overwritten.
  std::filesystem::create_hard_link(temp, path);
  return static_cast<std::size_t>(size);
}

}  // namespace palace
