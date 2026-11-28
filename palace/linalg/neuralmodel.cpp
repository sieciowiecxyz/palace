// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include "neuralmodel.hpp"

#include <algorithm>
#include <bit>
#include <cmath>
#include <cstring>
#include <exception>
#include <fstream>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <ATen/ATen.h>
#include <c10/core/InferenceMode.h>
#include <openssl/sha.h>
#if defined(PALACE_WITH_ML_CUDA)
#include <ATen/core/CachingHostAllocator.h>
#include <ATen/cuda/CUDAContextLight.h>
#include <c10/cuda/CUDACachingAllocator.h>
#include <c10/cuda/CUDAGuard.h>
#endif
#include <nlohmann/json.hpp>

namespace palace
{

namespace
{

using Json = nlohmann::json;

constexpr int Blocks = 6, Width = 16, Features = 7, Context = 3;
constexpr std::size_t WeightBytes = 73984, ManifestLimit = 1 << 20;
constexpr int PhiColumns = NeuralModel::PhiColumns,
              BasisColumns = NeuralModel::BasisColumns;

void Require(bool valid, const char *message)
{
  if (!valid)
  {
    throw std::runtime_error(message);
  }
}

std::vector<char> ReadBounded(const std::filesystem::path &path, std::size_t limit)
{
  Require(std::filesystem::is_regular_file(path), "Missing or nonregular model file");
  std::ifstream file(path, std::ios::binary);
  Require(file.is_open(), "Cannot open model file");
  std::vector<char> data(limit + 1);
  file.read(data.data(), data.size());
  Require(file.eof() && !file.bad(), "Model file exceeds limit or read failed");
  data.resize(file.gcount());
  return data;
}

Json ReadManifest(const std::filesystem::path &path)
{
  const auto data = ReadBounded(path, ManifestLimit);
  std::array<std::set<std::string>, 33> keys;
  return Json::parse(data.begin(), data.end(),
                     [&](int depth, Json::parse_event_t event, Json &value)
                     {
                       Require(depth < 32, "Model manifest exceeds nesting limit");
                       if (event == Json::parse_event_t::object_start)
                       {
                         keys[depth + 1].clear();
                       }
                       if (event == Json::parse_event_t::key)
                       {
                         Require(keys[depth].insert(value.get<std::string>()).second,
                                 "Duplicate model manifest key");
                       }
                       return true;
                     });
}

std::string Sha256(const std::vector<char> &data)
{
  unsigned char digest[SHA256_DIGEST_LENGTH];
  Require(SHA256(reinterpret_cast<const unsigned char *>(data.data()), data.size(), digest),
          "Cannot hash model weights");
  constexpr char hex[] = "0123456789abcdef";
  std::string hash;
  for (auto byte : digest)
  {
    hash += hex[byte >> 4];
    hash += hex[byte & 15];
  }
  return hash;
}

struct WeightEntry
{
  std::string name;
  std::vector<std::int64_t> shape;
  std::size_t offset;
};

std::vector<WeightEntry> WeightLayout()
{
  std::vector<WeightEntry> entries;
  std::size_t offset = 0;
  auto append = [&](std::string name, std::vector<std::int64_t> shape)
  {
    const auto count = shape.front() * (shape.size() == 2 ? shape.back() : 1);
    entries.push_back({std::move(name), std::move(shape), offset});
    offset += sizeof(double) * count;
  };
  auto complex_map = [&](const std::string &name, int rows, int columns)
  {
    append(name + ".real", {rows, columns});
    append(name + ".imag", {rows, columns});
  };
  complex_map("lift", PhiColumns, Width);
  for (int i = 0; i < Blocks; ++i)
  {
    const auto prefix = "blocks." + std::to_string(i);
    complex_map(prefix + ".local", Width, Width);
    complex_map(prefix + ".operator", Width, Width);
    append(prefix + ".gate.weight", {Width + Features + Context, Width});
    append(prefix + ".gate.bias", {Width});
  }
  complex_map("readout", Width, BasisColumns);
  Require(offset == WeightBytes, "Unsupported model weight layout");
  return entries;
}

std::vector<at::Tensor> LoadWeights(const std::filesystem::path &directory)
{
  static_assert(sizeof(double) == 8 && std::numeric_limits<double>::is_iec559);
  const auto layout = WeightLayout();
  Json tensors = Json::array();
  for (const auto &entry : layout)
  {
    tensors.push_back(
        {{"name", entry.name}, {"shape", entry.shape}, {"offset_bytes", entry.offset}});
  }
  const Json expected = {{"schema", "palace-neural-weights"},
                         {"version", 1},
                         {"dtype", "float64-le"},
                         {"normalization", "scalar-row-l1-v1"},
                         {"phi_version", "phi-global-nd-v1"},
                         {"architecture",
                          {{"blocks", Blocks},
                           {"complex_width", Width},
                           {"basis_k", BasisColumns},
                           {"phi_columns", PhiColumns},
                           {"row_features", Features},
                           {"context", Context}}},
                         {"scope",
                          {{"problem", "driven_uniform"},
                           {"mpi_ranks", 1},
                           {"coarse_space", "conforming_nd"},
                           {"coarse_order", 1}}},
                         {"tensors", std::move(tensors)}};
  const auto manifest = ReadManifest(directory / "manifest.json");
  for (const auto &[key, value] : expected.items())
  {
    // Compare serialized values to distinguish integral fields from JSON floats.
    Require(manifest.at(key).dump() == value.dump(), "Unsupported model manifest field");
  }

  const auto blob = ReadBounded(directory / "weights.bin", WeightBytes);
  const Json weights = {
      {"file", "weights.bin"}, {"bytes", WeightBytes}, {"sha256", Sha256(blob)}};
  Require(blob.size() == WeightBytes && manifest.at("weights").dump() == weights.dump(),
          "Invalid model weight size or SHA-256");

  std::vector<at::Tensor> params;
  for (const auto &entry : layout)
  {
    auto tensor =
        at::empty(entry.shape, at::TensorOptions().dtype(at::kDouble).device(at::kCPU));
    auto *dest = tensor.data_ptr<double>();
    for (std::int64_t i = 0; i < tensor.numel(); ++i)
    {
      std::uint64_t bits = 0;
      for (unsigned int byte = 0; byte < sizeof(double); ++byte)
      {
        const auto value = static_cast<unsigned char>(blob[entry.offset + i * 8 + byte]);
        bits |= static_cast<std::uint64_t>(value) << (byte * 8);
      }
      dest[i] = std::bit_cast<double>(bits);
      Require(std::isfinite(dest[i]), "Nonfinite model weight");
    }
    params.push_back(std::move(tensor));
  }
  return params;
}

template <typename T>
at::Tensor CopyToCpu(std::span<const T> data, at::IntArrayRef shape, at::ScalarType type)
{
  auto tensor = at::empty(shape, at::TensorOptions().dtype(type).device(at::kCPU));
  if (!data.empty())
  {
    std::memcpy(tensor.data_ptr<T>(), data.data(), data.size_bytes());
  }
  return tensor;
}

void ValidateInput(const NeuralModel::Input &input, const NeuralModel::Limits &limits)
{
  Require(input.indptr.size() > 1, "Empty model CSR");
  const auto rows = input.indptr.size() - 1;
  const auto nnz = input.indices.size();
  Require(rows <= limits.max_rows && nnz <= limits.max_nnz,
          "Model input exceeds size limits");

  // Include host and device copies, output and dense intermediates. The caller must
  // leave additional headroom for allocator reserves and backend-specific workspace.
  constexpr std::size_t Fixed = 4 * WeightBytes, PerRow = 4096, PerEntry = 64;
  std::size_t budget = limits.max_working_bytes;
  Require(budget >= Fixed && rows <= (budget - Fixed) / PerRow,
          "Model input exceeds working memory budget");
  budget -= Fixed + rows * PerRow;
  Require(nnz <= budget / PerEntry, "Model input exceeds working memory budget");

  Require(nnz == input.values.size() && input.indptr.front() == 0 &&
              input.indptr.back() == static_cast<std::int64_t>(nnz) &&
              std::is_sorted(input.indptr.begin(), input.indptr.end()),
          "Invalid model CSR offsets");
  Require(input.phi_real.size() == rows * PhiColumns &&
              input.phi_imag.size() == rows * PhiColumns,
          "Invalid model Phi shape");
  const auto [omega, shifted, real] = input.context;
  Require(std::isfinite(omega) && omega > 0 && (shifted == 0 || shifted == 1) &&
              (real == 0 || real == 1),
          "Invalid model context");

  Require(input.essential_tdofs.size() < rows, "Model requires free rows");
  int previous = -1;
  for (auto row : input.essential_tdofs)
  {
    Require(row > previous && static_cast<std::size_t>(row) < rows,
            "Invalid model essential DOFs");
    previous = row;
  }
}

struct Prepared
{
  at::Tensor offsets, indices, sparse_real, sparse_imag, features, free, phi;
};

Prepared Prepare(const NeuralModel::Input &input)
{
  const auto rows = static_cast<std::int64_t>(input.indptr.size() - 1);
  const auto nnz = static_cast<std::int64_t>(input.indices.size());
  const auto options = at::TensorOptions().dtype(at::kDouble).device(at::kCPU);
  auto free = at::ones({rows, 1}, options);
  auto *free_data = free.data_ptr<double>();
  for (auto row : input.essential_tdofs)
  {
    free_data[row] = 0.0;
  }

  auto features = at::zeros({rows, Features}, options);
  auto *feature = features.data_ptr<double>();
  double scale = 0.0;
  for (std::int64_t row = 0; row < rows; ++row, feature += Features)
  {
    std::int64_t previous = -1;
    const auto start = input.indptr[row], end = input.indptr[row + 1];
    for (auto pos = start; pos < end; ++pos)
    {
      const auto col = input.indices[pos];
      const auto value = input.values[pos];
      Require(col > previous && col < rows && std::isfinite(value.real()) &&
                  std::isfinite(value.imag()),
              "Invalid model CSR column or value");
      previous = col;
      feature[2] += std::abs(value);
      if (col == row)
      {
        feature[0] = value.real();
        feature[1] = value.imag();
      }
    }
    Require(std::isfinite(feature[2]), "Nonfinite model CSR row sum");
    if (free_data[row])
    {
      scale = std::max(scale, feature[2]);
    }
    feature[5] = std::log1p(end - start);
    feature[6] = 1.0 - free_data[row];
    for (int col = 0; col < PhiColumns; ++col)
    {
      const auto r = input.phi_real[row * PhiColumns + col];
      const auto i = input.phi_imag[row * PhiColumns + col];
      Require(std::isfinite(r) && std::isfinite(i) &&
                  (free_data[row] || (r == 0 && i == 0)),
              "Invalid model Phi or essential row");
    }
  }
  Require(scale > 0.0, "Invalid model CSR normalization scale");

  auto sparse_real = at::empty({nnz}, options);
  auto sparse_imag = at::empty({nnz}, options);
  auto *real = sparse_real.data_ptr<double>();
  auto *imag = sparse_imag.data_ptr<double>();
  feature = features.data_ptr<double>();
  for (std::int64_t row = 0; row < rows; ++row, feature += Features)
  {
    for (int i = 0; i < 3; ++i)
    {
      feature[i] /= scale;
      Require(std::isfinite(feature[i]), "Nonfinite normalized model feature");
    }
    for (auto pos = input.indptr[row]; pos < input.indptr[row + 1]; ++pos)
    {
      real[pos] = input.values[pos].real() / scale;
      imag[pos] = input.values[pos].imag() / scale;
      const double magnitude = std::hypot(real[pos], imag[pos]);
      feature[3] += magnitude * magnitude;
      if (input.indices[pos] != row)
      {
        feature[4] += magnitude;
      }
    }
    Require(std::isfinite(feature[3]) && std::isfinite(feature[4]),
            "Nonfinite normalized model CSR or row features");
    feature[3] = std::sqrt(feature[3]);
  }
  return {CopyToCpu(input.indptr, {rows + 1}, at::kLong),
          CopyToCpu(input.indices, {nnz}, at::kLong),
          std::move(sparse_real),
          std::move(sparse_imag),
          std::move(features),
          std::move(free),
          at::complex(CopyToCpu(input.phi_real, {rows, PhiColumns}, at::kDouble),
                      CopyToCpu(input.phi_imag, {rows, PhiColumns}, at::kDouble))};
}

at::Device SelectDevice(NeuralModel::Device requested)
{
  switch (requested.backend)
  {
    case NeuralModel::Backend::Cpu:
      Require(requested.index == 0, "CPU model device index must be zero");
      return at::Device(at::kCPU);
    case NeuralModel::Backend::Cuda:
      Require(requested.index >= 0 &&
                  requested.index <= std::numeric_limits<c10::DeviceIndex>::max(),
              "Invalid CUDA model device index");
      return at::Device(at::kCUDA, static_cast<c10::DeviceIndex>(requested.index));
  }
  throw std::runtime_error("Unsupported model device");
}

}  // namespace

struct NeuralModel::Impl
{
  explicit Impl(const std::filesystem::path &directory) : weights(LoadWeights(directory)) {}

  Basis Evaluate(const Input &input, at::Device device) const;

  const std::vector<at::Tensor> weights;
};

NeuralModel::NeuralModel(const std::filesystem::path &directory)
  : impl(std::make_unique<Impl>(directory))
{
}

NeuralModel::~NeuralModel() = default;

NeuralModel::Basis NeuralModel::Impl::Evaluate(const Input &input, at::Device device) const
{
  auto data = Prepare(input);
  auto offsets = data.offsets.to(device), indices = data.indices.to(device);
  const auto rows = data.phi.size(0);
  auto csr = [&](const at::Tensor &cpu_values)
  {
    auto values = cpu_values.to(device);
    return at::sparse_csr_tensor(offsets, indices, values, {rows, rows},
                                 values.options().layout(at::kSparseCsr));
  };
  const auto sparse_real = csr(data.sparse_real), sparse_imag = csr(data.sparse_imag);
  auto sparse = [&](const at::Tensor &h)
  {
    const auto real = at::real(h).contiguous(), imag = at::imag(h).contiguous();
    return at::complex(at::mm(sparse_real, real) - at::mm(sparse_imag, imag),
                       at::mm(sparse_real, imag) + at::mm(sparse_imag, real));
  };
  const auto context =
      CopyToCpu<double>(input.context, {1, Context}, at::kDouble).to(device);
  const auto invariant =
      at::cat({data.features.to(device), context.expand({rows, Context})}, 1);
  const auto free = data.free.to(device);

  auto param = weights.begin();
  auto next = [&]() { return (param++)->to(device); };
  auto complex_map = [&]()
  {
    auto real = next();
    return at::complex(real, next());
  };
  auto h = at::mm(data.phi.to(device), complex_map());
  for (int i = 0; i < Blocks; ++i)
  {
    const auto local = complex_map(), op = complex_map();
    const auto weight = next(), bias = next();
    const auto gate =
        at::sigmoid(at::mm(at::cat({at::abs(h), invariant}, 1), weight) + bias);
    h = free * (h + gate * (at::mm(h, local) + at::mm(sparse(h), op)));
  }
  // Blocking transfer completes model work before returning owned host output.
  const auto output = (free * at::mm(h, complex_map())).to(at::kCPU);
  Require(at::isfinite(output).all().item<bool>(), "Nonfinite model basis");
  const auto real = at::real(output).contiguous();
  const auto imag = at::imag(output).contiguous();
  const auto count = output.numel();
  return {{real.data_ptr<double>(), real.data_ptr<double>() + count},
          {imag.data_ptr<double>(), imag.data_ptr<double>() + count}};
}

NeuralModel::Basis NeuralModel::Infer(const Input &input, const Limits &limits,
                                      Device requested) const
{
  ValidateInput(input, limits);
  const c10::InferenceMode inference;
  const auto device = SelectDevice(requested);
  if (device.is_cpu())
  {
    return impl->Evaluate(input, device);
  }

#if defined(PALACE_WITH_ML_CUDA)
  int count = 0;
  const auto status = cudaGetDeviceCount(&count);
  Require(status != cudaErrorNoDevice, "CUDA model device unavailable");
  if (status != cudaSuccess)
  {
    throw CudaHandoffError(std::string("Cannot query CUDA model devices: ") +
                           cudaGetErrorString(status));
  }
  Require(device.index() < count, "CUDA model device unavailable");
  c10::cuda::OptionalCUDAStreamGuard guard;
  NeuralModel::Basis basis;
  std::exception_ptr inference_error;
  try
  {
    guard.reset_stream(c10::cuda::getDefaultCUDAStream(device.index()));
  }
  catch (const std::exception &e)
  {
    throw CudaHandoffError(std::string("Cannot select CUDA model stream: ") + e.what());
  }

  try
  {
    basis = impl->Evaluate(input, device);
  }
  catch (...)
  {
    inference_error = std::current_exception();
  }

  // Evaluate has released all temporary tensor owners, including on exception.
  // Clear Torch-owned workspace references before releasing cached blocks.
  try
  {
    const auto pending = cudaGetLastError();
    if (pending != cudaSuccess && pending != cudaErrorMemoryAllocation)
    {
      throw std::runtime_error(cudaGetErrorString(pending));
    }
    guard.current_stream()->synchronize();
    at::cuda::clearCublasWorkspaces();
    at::getHostAllocator(at::kCUDA)->empty_cache();
    c10::cuda::CUDACachingAllocator::emptyCache();
  }
  catch (const std::exception &e)
  {
    throw CudaHandoffError(std::string("CUDA model handoff failed: ") + e.what());
  }

  if (inference_error)
  {
    std::rethrow_exception(inference_error);
  }
  return basis;
#else
  throw std::runtime_error("CUDA model inference is unavailable in this build");
#endif
}

}  // namespace palace
