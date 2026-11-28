// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include "warmstartmodel.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <nlohmann/json.hpp>
#include "linalg/vector.hpp"

namespace palace
{

namespace
{

using Json = nlohmann::json;

constexpr int max_dofs = 16384;
constexpr int max_rank = 32;
constexpr std::streamoff max_bundle_bytes = 32 * 1024 * 1024;

Json ReadBundle(const std::filesystem::path &path)
{
  if (!std::filesystem::is_regular_file(path))
  {
    throw std::runtime_error("Warm-start model path must be a regular file");
  }

  std::ifstream file(path, std::ios::binary | std::ios::ate);
  const auto size = file.tellg();
  if (size <= 0 || size > max_bundle_bytes)
  {
    throw std::runtime_error("Warm-start model must be readable and at most 32 MiB");
  }

  std::string data(static_cast<std::size_t>(size), '\0');
  file.seekg(0);
  if (!file.read(data.data(), data.size()) ||
      file.peek() != std::char_traits<char>::eof() || file.bad())
  {
    throw std::runtime_error("Could not read complete warm-start model");
  }
  if (data.find('\0') != std::string::npos)
  {
    throw std::runtime_error("Warm-start model contains a literal NUL byte");
  }

  // The schema uses at most five nested containers. Bound parser depth for
  // invalid files.
  return Json::parse(data,
                     [](int depth, Json::parse_event_t, Json &)
                     {
                       if (depth > 8)
                       {
                         throw std::runtime_error(
                             "Warm-start model JSON is too deeply nested");
                       }
                       return true;
                     });
}

int ReadInt(const Json &value, const char *field)
{
  if (value.is_number_unsigned())
  {
    const auto number = value.get<Json::number_unsigned_t>();
    if (number <= std::numeric_limits<int>::max())
    {
      return static_cast<int>(number);
    }
  }
  else if (value.is_number_integer())
  {
    const auto number = value.get<Json::number_integer_t>();
    if (number >= std::numeric_limits<int>::min() &&
        number <= std::numeric_limits<int>::max())
    {
      return static_cast<int>(number);
    }
  }
  throw std::runtime_error(std::string("Invalid warm-start model integer: ") + field);
}

void CheckShape(const Json &value, std::size_t count, const char *field)
{
  if (!value.is_array() || value.size() != count)
  {
    throw std::runtime_error(std::string("Invalid warm-start model array shape: ") + field);
  }
}

double ReadNumber(const Json &value, const char *field)
{
  if (value.is_number())
  {
    const double number = value.get<double>();
    if (std::isfinite(number))
    {
      return number;
    }
  }
  throw std::runtime_error(std::string("Invalid warm-start model number: ") + field);
}

template <typename Iterator>
void ReadRow(const Json &value, int count, const char *field, Iterator out)
{
  CheckShape(value, count, field);
  for (const auto &entry : value)
  {
    *out++ = ReadNumber(entry, field);
  }
}

std::vector<double> ReadMatrix(const Json &value, int rows, int cols, const char *field)
{
  CheckShape(value, rows, field);
  std::vector<double> matrix(rows * cols);
  for (int row = 0; row < rows; row++)
  {
    ReadRow(value[row], cols, field, matrix.begin() + row * cols);
  }
  return matrix;
}

double SiLU(double value)
{
  if (value >= 0.0)
  {
    return value / (1.0 + std::exp(-value));
  }
  const double exp_value = std::exp(value);
  return value * exp_value / (1.0 + exp_value);
}

}  // namespace

WarmStartModel::WarmStartModel(const std::filesystem::path &path,
                               const std::string &space_id, int n)
  : n(n)
{
  if (n <= 0 || n > max_dofs || space_id.empty())
  {
    throw std::invalid_argument("Invalid warm-start model space");
  }

  const auto model = ReadBundle(path);
  if (model.at("schema") != "palace-warmstart-model-v1")
  {
    throw std::runtime_error("Unsupported warm-start model schema");
  }
  if (model.at("space_id") != space_id || ReadInt(model.at("n"), "n") != n)
  {
    throw std::runtime_error("Warm-start model does not match the finite-element space");
  }

  rank = ReadInt(model.at("rank"), "rank");
  if (rank <= 0 || rank > max_rank)
  {
    throw std::runtime_error("Warm-start model rank must be between 1 and 32");
  }

  const auto &model_excitations = model.at("excitations");
  if (!model_excitations.is_array() || model_excitations.empty())
  {
    throw std::runtime_error("Warm-start model must list supported excitations");
  }
  excitations.reserve(model_excitations.size());
  for (const auto &entry : model_excitations)
  {
    excitations.push_back(ReadInt(entry, "excitations"));
  }
  std::sort(excitations.begin(), excitations.end());

  ReadRow(model.at("mean"), feature_count, "mean", mean.begin());
  ReadRow(model.at("scale"), feature_count, "scale", scale.begin());
  for (double deviation : scale)
  {
    if (deviation <= 0.0)
    {
      throw std::runtime_error("Warm-start model scales must be positive");
    }
  }
  basis = ReadMatrix(model.at("basis"), n, rank, "basis");

  const auto &model_layers = model.at("layers");
  CheckShape(model_layers, layers.size(), "layers");
  int input_width = feature_count;
  for (std::size_t i = 0; i < layers.size(); i++)
  {
    const int output_width = (i + 1 == layers.size()) ? 2 * rank : hidden_width;
    const auto &layer = model_layers[i];
    layers[i].weight = ReadMatrix(layer.at("weight"), output_width, input_width, "weight");
    layers[i].bias.resize(output_width);
    ReadRow(layer.at("bias"), output_width, "bias", layers[i].bias.begin());
    input_width = output_width;
  }
}

bool WarmStartModel::Predict(double omega, int excitation, double rhs_norm,
                             ComplexVector &candidate) const
{
  if (!std::isfinite(omega) || !std::isfinite(rhs_norm) || rhs_norm < 0.0 ||
      !std::binary_search(excitations.begin(), excitations.end(), excitation))
  {
    return false;
  }

  std::array<double, hidden_width> activations{omega, static_cast<double>(excitation),
                                               std::log1p(rhs_norm)};
  std::array<double, hidden_width> output{};
  for (int i = 0; i < feature_count; i++)
  {
    activations[i] = (activations[i] - mean[i]) / scale[i];
    if (!std::isfinite(activations[i]))
    {
      return false;
    }
  }

  int input_width = feature_count;
  for (std::size_t i = 0; i < layers.size(); i++)
  {
    const auto &layer = layers[i];
    const bool hidden = i + 1 < layers.size();
    for (std::size_t row = 0; row < layer.bias.size(); row++)
    {
      const double value =
          std::inner_product(activations.begin(), activations.begin() + input_width,
                             layer.weight.begin() + row * input_width, layer.bias[row]);
      if (!std::isfinite(value))
      {
        return false;
      }
      output[row] = hidden ? SiLU(value) : value;
    }
    activations.swap(output);
    input_width = layer.bias.size();
  }

  std::vector<double> real(n), imag(n);
  for (int row = 0; row < n; row++)
  {
    const auto start = basis.begin() + row * rank;
    real[row] = std::inner_product(start, start + rank, activations.begin(), 0.0);
    imag[row] = std::inner_product(start, start + rank, activations.begin() + rank, 0.0);
    if (!std::isfinite(real[row]) || !std::isfinite(imag[row]))
    {
      return false;
    }
  }

  // HostWrite invalidates any stale device copy while preserving the device-use
  // flag.
  candidate.SetSize(n);
  std::copy(real.begin(), real.end(), candidate.Real().HostWrite());
  std::copy(imag.begin(), imag.end(), candidate.Imag().HostWrite());
  return true;
}

}  // namespace palace
