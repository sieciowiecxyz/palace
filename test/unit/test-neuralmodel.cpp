// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include <algorithm>
#include <array>
#include <bit>
#include <complex>
#include <cstdint>
#include <fstream>
#include <limits>
#include <string>
#include <vector>
#include <catch2/catch_test_macros.hpp>
#include <nlohmann/json.hpp>
#include "fixtures.hpp"
#include "linalg/neuralmodel.hpp"
#if defined(PALACE_WITH_ML_CUDA)
#include "linalg/vector.hpp"
#endif

namespace palace
{
namespace
{
using Complex = std::complex<double>;
using nlohmann::json;

struct ModelFixture : test::PerRankTempDir
{
  static constexpr int Rows = 3;
  static constexpr int Phi = NeuralModel::PhiColumns;
  static constexpr int Basis = NeuralModel::BasisColumns;
  static constexpr NeuralModel::Device Cpu{NeuralModel::Backend::Cpu, 0};
  const NeuralModel::Limits limits{Rows, 7, 1 << 20};
  std::array<std::int64_t, Rows + 1> offsets{0, 3, 6, 7};
  std::array<std::int64_t, 7> columns{0, 1, 2, 0, 1, 2, 2};
  std::array<Complex, 7> values{
      {{2, 1}, {-1, 2}, {1, 0}, {0.5, -1}, {3, 0}, {-2, 0}, {100, 0}}};
  std::array<int, 1> essential{2};
  std::array<double, Rows * Phi> real{}, imag{};
  json manifest;

  ModelFixture()
  {
    real[0] = 1.0;
    imag[0] = 2.0;
    real[Phi] = -2.0;
    imag[Phi] = 1.0;

    // One channel survives. In block 0 the zero gate logits give sigmoid(0) = 1/2.
    // The other five blocks are identity on free rows.
    constexpr int width = 16, blocks = 6;
    json tensors = json::array();
    std::vector<unsigned char> blob;
    auto tensor = [&](const std::string &name, std::vector<int> shape, int index = 0,
                      double weight = 0.0)
    {
      tensors.push_back({{"name", name}, {"shape", shape}, {"offset_bytes", blob.size()}});
      const int count = shape.front() * (shape.size() == 2 ? shape.back() : 1);
      for (int i = 0; i < count; ++i)
      {
        const auto bits = std::bit_cast<std::uint64_t>(i == index ? weight : 0.0);
        for (int byte = 0; byte < 8; ++byte)
        {
          blob.push_back(static_cast<unsigned char>(bits >> (8 * byte)));
        }
      }
    };
    tensor("lift.real", {Phi, width}, 0, 1.0);
    tensor("lift.imag", {Phi, width}, 0, -0.5);
    for (int block = 0; block < blocks; ++block)
    {
      const auto prefix = "blocks." + std::to_string(block);
      tensor(prefix + ".local.real", {width, width});
      tensor(prefix + ".local.imag", {width, width});
      tensor(prefix + ".operator.real", {width, width}, 0, block == 0 ? 0.5 : 0.0);
      tensor(prefix + ".operator.imag", {width, width}, 0, block == 0 ? 1.0 : 0.0);
      tensor(prefix + ".gate.weight", {width + 7 + 3, width});
      tensor(prefix + ".gate.bias", {width});
    }
    tensor("readout.real", {width, Basis}, 3, -1.0);
    tensor("readout.imag", {width, Basis}, 3, 0.25);
    manifest = {
        {"schema", "palace-neural-weights"},
        {"version", 1},
        {"dtype", "float64-le"},
        {"normalization", "scalar-row-l1-v1"},
        {"phi_version", "phi-global-nd-v1"},
        {"architecture",
         {{"blocks", blocks},
          {"complex_width", width},
          {"basis_k", Basis},
          {"phi_columns", Phi},
          {"row_features", 7},
          {"context", 3}}},
        {"scope",
         {{"problem", "driven_uniform"},
          {"mpi_ranks", 1},
          {"coarse_space", "conforming_nd"},
          {"coarse_order", 1}}},
        {"tensors", tensors},
        {"weights",
         {{"file", "weights.bin"},
          {"bytes", blob.size()},
          {"sha256", "3ecc2fc8e93a8c4a60077699e9fde3657508c05c579a575ade186ad902c1308c"}}}};
    std::ofstream weights(temp_dir / "weights.bin", std::ios::binary);
    weights.write(reinterpret_cast<const char *>(blob.data()), blob.size());
    weights.close();
    REQUIRE(weights.good());
    WriteManifest();
  }

  void WriteManifest()
  {
    std::ofstream output(temp_dir / "manifest.json");
    output << manifest;
    output.close();
    REQUIRE(output.good());
  }

  NeuralModel::Input Input() const
  {
    return {offsets, columns, values, essential, real, imag, {0.75, 1.0, 0.0}};
  }

  static Complex At(const NeuralModel::Basis &basis, int row, int column)
  {
    return {basis.real[row * Basis + column], basis.imag[row * Basis + column]};
  }
};
}  // namespace

TEST_CASE_METHOD(ModelFixture,
                 "Neural model CPU CSR inference preserves phase and orientation",
                 "[Serial][NeuralModel]")
{
  NeuralModel model(temp_dir);
  const auto output = model.Infer(Input(), limits, Cpu);
  REQUIRE(output.real.size() == Rows * Basis);
  REQUIRE(output.imag.size() == Rows * Basis);

  const double scale = std::abs(values[3]) + std::abs(values[4]) + std::abs(values[5]);
  const Complex h0 = Complex(1, -0.5) * Complex(real[0], imag[0]);
  const Complex h1 = Complex(1, -0.5) * Complex(real[Phi], imag[Phi]);
  const auto expected = [&](Complex h, Complex a0, Complex a1)
  { return Complex(-1, 0.25) * (h + 0.5 * Complex(0.5, 1) * (a0 * h0 + a1 * h1) / scale); };
  CHECK(std::abs(At(output, 0, 3) - expected(h0, values[0], values[1])) < 1.0e-12);
  CHECK(std::abs(At(output, 1, 3) - expected(h1, values[3], values[4])) < 1.0e-12);

  // A signed change of orientation transforms the input as (D A D, D Phi).
  // Combine it with a global phase to exercise complex channels and off-diagonal signs.
  const Complex phase(0.6, -0.8);
  constexpr std::array<int, Rows> sign{-1, 1, 1};
  for (int row = 0; row < Rows; ++row)
  {
    const auto z =
        static_cast<double>(sign[row]) * phase * Complex(real[row * Phi], imag[row * Phi]);
    real[row * Phi] = z.real();
    imag[row * Phi] = z.imag();
    for (auto pos = offsets[row]; pos < offsets[row + 1]; ++pos)
    {
      values[pos] *= sign[row] * sign[columns[pos]];
    }
  }
  const auto transformed = model.Infer(Input(), limits, Cpu);
  for (int row = 0; row < Rows; ++row)
  {
    for (int col = 0; col < Basis; ++col)
    {
      const auto z = At(output, row, col);
      if (row == essential.front() || col != 3)
      {
        CHECK(z == Complex{});
        CHECK(At(transformed, row, col) == Complex{});
      }
      else
      {
        CHECK(std::abs(At(transformed, row, col) -
                       static_cast<double>(sign[row]) * phase * z) < 1.0e-12);
      }
    }
  }
}

#if defined(PALACE_WITH_ML_CUDA)
TEST_CASE_METHOD(ModelFixture, "Neural model cold CUDA inference hands off to MFEM",
                 "[Serial][GPU][NeuralModel]")
{
  if (!mfem::Device::Allows(mfem::Backend::CUDA_MASK))
  {
    SKIP("Requires the CUDA device");
  }

  NeuralModel model(temp_dir);
  // Let Infer initialize ATen CUDA on its first call in the isolated test process.
  const NeuralModel::Device cuda{NeuralModel::Backend::Cuda, mfem::Device::GetId()};
  const auto gpu = model.Infer(Input(), limits, cuda);
  REQUIRE(gpu.real.size() == Rows * Basis);
  REQUIRE(gpu.imag.size() == Rows * Basis);

  // Consume the returned host basis through MFEM's device memory and kernel paths
  // immediately after Infer. HostRead also checks the device-to-host handoff.
  ComplexVector handed_off(Rows * Basis);
  handed_off.UseDevice(true);
  std::copy(gpu.real.begin(), gpu.real.end(), handed_off.Real().HostWrite());
  std::copy(gpu.imag.begin(), gpu.imag.end(), handed_off.Imag().HostWrite());
  const Complex factor(0.6, -0.8);
  handed_off *= factor;
  const auto *result_real = handed_off.Real().HostRead();
  const auto *result_imag = handed_off.Imag().HostRead();

  const auto cpu = model.Infer(Input(), limits, Cpu);
  REQUIRE(cpu.real.size() == Rows * Basis);
  REQUIRE(cpu.imag.size() == Rows * Basis);
  for (int row = 0; row < Rows; ++row)
  {
    for (int col = 0; col < Basis; ++col)
    {
      CAPTURE(row, col);
      const int i = row * Basis + col;
      const Complex reference = At(cpu, row, col);
      CHECK(std::abs(At(gpu, row, col) - reference) < 1.0e-12);
      CHECK(std::abs(Complex(result_real[i], result_imag[i]) - factor * reference) <
            1.0e-12);
      if (row == essential.front())
      {
        CHECK(At(gpu, row, col) == Complex{});
      }
    }
  }
}
#endif

TEST_CASE_METHOD(ModelFixture, "Neural model rejects invalid bundles",
                 "[Serial][NeuralModel]")
{
  REQUIRE_NOTHROW(NeuralModel{temp_dir});
  SECTION("Unsupported schema version")
  {
    manifest["version"] = 2;
    WriteManifest();
    CHECK_THROWS(NeuralModel{temp_dir});
  }
  SECTION("Wrong tensor offset")
  {
    manifest["tensors"][0]["offset_bytes"] = 8;
    WriteManifest();
    CHECK_THROWS(NeuralModel{temp_dir});
  }
  SECTION("Same-size payload with wrong digest")
  {
    std::fstream weights(temp_dir / "weights.bin",
                         std::ios::in | std::ios::out | std::ios::binary);
    weights.put('\x01');
    weights.close();
    REQUIRE(weights.good());
    CHECK_THROWS(NeuralModel{temp_dir});
  }
  SECTION("Truncated payload")
  {
    std::filesystem::resize_file(temp_dir / "weights.bin", 128);
    CHECK_THROWS(NeuralModel{temp_dir});
  }
}

TEST_CASE_METHOD(ModelFixture, "Neural model rejects inadmissible CPU inputs",
                 "[Serial][NeuralModel]")
{
  NeuralModel model(temp_dir);
  SECTION("Duplicate CSR column")
  {
    columns[1] = columns[0];
  }
  SECTION("Nonfinite CSR value")
  {
    values[1] = {0.0, std::numeric_limits<double>::infinity()};
  }
  SECTION("Phi has a nonzero essential row")
  {
    imag[essential.front() * Phi] = 1.0;
  }
  CHECK_THROWS(model.Infer(Input(), limits, Cpu));
}

TEST_CASE_METHOD(ModelFixture, "Neural model observes CPU admission limits",
                 "[Serial][NeuralModel]")
{
  NeuralModel model(temp_dir);
  CHECK_THROWS(
      model.Infer(Input(), {Rows - 1, limits.max_nnz, limits.max_working_bytes}, Cpu));
  CHECK_THROWS(
      model.Infer(Input(), {Rows, limits.max_nnz - 1, limits.max_working_bytes}, Cpu));
  CHECK_THROWS(model.Infer(Input(), {Rows, limits.max_nnz, 1}, Cpu));
  CHECK_NOTHROW(model.Infer(Input(), limits, Cpu));
}
}  // namespace palace
