// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_UTILS_PORTADJOINT_HPP
#define PALACE_UTILS_PORTADJOINT_HPP

#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include "fem/gridfunction.hpp"
#include "linalg/operator.hpp"
#include "linalg/vector.hpp"
#include "models/spaceoperator.hpp"
#include "utils/communication.hpp"
#include "utils/iodata.hpp"

namespace palace
{

// Research-only, single-frequency true-DOF probe. The frozen launcher binds each
// input to mesh connectivity, FE ordering, frequency, binary and field hashes.
// Ordinary runs allocate no probe fields and do not write probe output.
class PortAdjointProbe
{
  SpaceOperator &space;
  double omega;
  double frequency_ghz = 0.0, linear_tol = 0.0;
  std::uint64_t ordering_hash = 0;
  std::filesystem::path output, input;
  std::vector<int> ports;
  std::map<int, std::unique_ptr<ComplexVector>> fields;
  bool enabled = false, operator_only = false, written = false;

  static nlohmann::json Pair(std::complex<double> value)
  {
    MFEM_VERIFY(std::isfinite(value.real()) && std::isfinite(value.imag()),
                "Nonfinite adjoint contraction!");
    return nlohmann::json::array({value.real(), value.imag()});
  }

  static void Snapshot(const std::filesystem::path &path, ComplexVector &field, bool save)
  {
    const std::array<char, 8> magic{'P', 'A', 'L', 'A', 'D', 'J', '0', '1'};
    const std::uint64_t count = field.Size();
    if (save)
    {
      MFEM_VERIFY(!std::filesystem::exists(path), "Refusing to overwrite probe field!");
      const auto temp = path.string() + ".tmp";
      std::ofstream stream(temp, std::ios::binary | std::ios::trunc);
      stream.write(magic.data(), magic.size());
      stream.write(reinterpret_cast<const char *>(&count), sizeof(count));
      stream.write(reinterpret_cast<const char *>(field.Real().HostRead()),
                   count * sizeof(double));
      stream.write(reinterpret_cast<const char *>(field.Imag().HostRead()),
                   count * sizeof(double));
      stream.close();
      MFEM_VERIFY(stream, "Failed to write adjoint field!");
      std::filesystem::rename(temp, path);
    }
    else
    {
      MFEM_VERIFY(std::filesystem::file_size(path) ==
                      magic.size() + sizeof(count) + 2 * count * sizeof(double),
                  "Adjoint field size does not match true-DOF space!");
      std::ifstream stream(path, std::ios::binary);
      std::array<char, 8> found{};
      std::uint64_t size = 0;
      stream.read(found.data(), found.size());
      stream.read(reinterpret_cast<char *>(&size), sizeof(size));
      MFEM_VERIFY(found == magic && size == count, "Invalid adjoint field header!");
      stream.read(reinterpret_cast<char *>(field.Real().HostWrite()),
                  count * sizeof(double));
      stream.read(reinterpret_cast<char *>(field.Imag().HostWrite()),
                  count * sizeof(double));
      MFEM_VERIFY(stream, "Failed to read adjoint field!");
    }
    const auto *real = field.Real().HostRead(), *imag = field.Imag().HostRead();
    for (std::uint64_t k = 0; k < count; ++k)
      MFEM_VERIFY(std::isfinite(real[k]) && std::isfinite(imag[k]),
                  "Nonfinite adjoint field!");
  }

  void Evaluate(const ComplexOperator &A, const char *mode)
  {
    MFEM_VERIFY(!written && fields.size() == ports.size(),
                "Incomplete/duplicate probe fields!");
    const auto start = std::chrono::steady_clock::now();
    ComplexVector applied(A.Height()), rhs(A.Height());
    applied.UseDevice(true);
    rhs.UseDevice(true);
    GridFunction view(space.GetNDSpace(), true);
    nlohmann::json contractions = nlohmann::json::array();
    nlohmann::json residuals = nlohmann::json::array();
    for (const int p : ports)
    {
      auto &ep = *fields.at(p);
      A.Mult(ep, applied);
      space.GetExcitationVector(p, omega, rhs);
      if (!operator_only)
      {
        ComplexVector residual(applied);
        residual -= rhs;
        const double rhs_norm = linalg::Norml2(space.GetComm(), rhs);
        const double relative = linalg::Norml2(space.GetComm(), residual) / rhs_norm;
        MFEM_VERIFY(rhs_norm > 0.0 && std::isfinite(relative) && relative <= linear_tol,
                    "Adjoint capture requires a converged true-RHS residual!");
        residuals.push_back({{"port", p}, {"relative", relative}});
      }
      view.Real().SetFromTrueDofs(ep.Real());
      view.Imag().SetFromTrueDofs(ep.Imag());
      for (const int q : ports)
      {
        auto &eq = *fields.at(q);
        const auto raw_mode = space.GetLumpedPortOp().GetPort(q).GetSParameter(view);
        contractions.push_back({{"source_port", p},
                                {"read_port", q},
                                {"E_transpose_A_E", Pair(eq.TransposeDot(applied))},
                                {"E_hermitian_A_E", Pair(applied.Dot(eq))},
                                {"E_transpose_rhs", Pair(eq.TransposeDot(rhs))},
                                {"raw_port_mode", Pair(raw_mode)}});
      }
    }
    nlohmann::json report = {
        {"schema", 1},
        {"mode", mode},
        {"omega_internal", omega},
        {"frequency_ghz", frequency_ghz},
        {"linear_tolerance", linear_tol},
        {"true_rhs_residuals", residuals},
        {"dof_ordering_hash", ordering_hash},
        {"true_dofs", A.Height()},
        {"port_indices", ports},
        {"field_bytes", 2ULL * sizeof(double) * A.Height() * ports.size()},
        {"contractions", contractions},
        {"contraction_seconds",
         std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count()},
        {"rf_validated", false}};
    const auto path = output / "contractions.json";
    std::ofstream stream(path.string() + ".tmp");
    stream << report.dump(2) << '\n';
    stream.close();
    MFEM_VERIFY(stream, "Failed to write adjoint contractions!");
    std::filesystem::rename(path.string() + ".tmp", path);
    written = true;
    Mpi::Print("PALACE_PORT_ADJOINT: mode={} ports={} dofs={} RF_VALIDATED=0\n", mode,
               ports.size(), A.Height());
  }

public:
  PortAdjointProbe(const IoData &data, SpaceOperator &space, double omega)
    : space(space), omega(omega)
  {
    const char *capture = std::getenv("PALACE_ADJOINT_CAPTURE");
    const char *source = std::getenv("PALACE_ADJOINT_INPUT");
    const char *destination = std::getenv("PALACE_ADJOINT_OUTPUT");
    enabled = capture || source || destination;
    if (!enabled)
      return;
    frequency_ghz =
        data.units.Dimensionalize<Units::ValueType::FREQUENCY>(omega) / (2 * M_PI);
    linear_tol = data.solver.linear.tol;
    MFEM_VERIFY((capture && !source && !destination) || (!capture && source && destination),
                "Use capture alone, or adjoint input/output together!");
    MFEM_VERIFY(
        Mpi::Size(space.GetComm()) == 1 && data.model.refinement.max_it == 0 &&
            data.solver.driven.restart == 1 && data.solver.driven.sample_f.size() == 1 &&
            data.solver.driven.adaptive_tol <= 0 && data.solver.order == 2 &&
            data.solver.pa_order_threshold == 1 && space.GetWavePortOp().Size() == 0 &&
            space.GetFloquetPortOp().Size() == 0,
        "Adjoint probe requires rank1/fixed mesh/P2/PA1/one frequency/lumped ports!");
    for (const auto &[index, spec] : space.GetPortExcitations())
    {
      const auto [simple, type, port] = spec.IsSimple();
      MFEM_VERIFY(simple && type == PortType::LumpedPort && index == port &&
                      space.GetLumpedPortOp().GetPort(port).GetExcitationRefResistance() >
                          0,
                  "Probe requires separate positive-reference lumped-port excitations!");
      ports.push_back(port);
    }
    MFEM_VERIFY((ports == std::vector<int>{1, 2}) && space.GetLumpedPortOp().Size() == 2,
                "Initial adjoint pilot requires exactly two active ports!");
    // Structural fingerprint, not a security hash: detect a changed FE numbering
    // even when a morphed mesh preserves node count and input connectivity.
    ordering_hash = 14695981039346656037ULL;
    const auto append = [this](std::int64_t value)
    {
      const auto word = static_cast<std::uint64_t>(value);
      for (int b = 0; b < 8; ++b)
      {
        ordering_hash ^= (word >> (8 * b)) & 255ULL;
        ordering_hash *= 1099511628211ULL;
      }
    };
    auto &fes = space.GetNDSpace().Get();
    append(fes.GetTrueVSize());
    append(fes.GetNE());
    mfem::Array<int> dofs;
    for (int element = 0; element < fes.GetNE(); ++element)
    {
      fes.GetElementDofs(element, dofs);
      append(dofs.Size());
      for (int dof : dofs)
        append(dof);
    }
    operator_only = source != nullptr;
    output = capture ? capture : destination;
    MFEM_VERIFY(std::filesystem::create_directory(output),
                "Probe output must be a fresh directory!");
    if (source)
    {
      input = source;
      const auto info_path = input / "contractions.json";
      std::ifstream stream(info_path);
      nlohmann::json info;
      stream >> info;
      MFEM_VERIFY(stream && info.at("schema") == 1 && info.at("mode") == "capture" &&
                      info.at("omega_internal").get<double>() == omega &&
                      info.at("port_indices").get<std::vector<int>>() == ports &&
                      info.at("dof_ordering_hash").get<std::uint64_t>() == ordering_hash &&
                      info.at("true_dofs").get<int>() == space.GetNDSpace().GetTrueVSize(),
                  "Input probe rank/space/frequency/port contract mismatch!");
      for (const int p : ports)
      {
        fields[p] = std::make_unique<ComplexVector>(space.GetNDSpace().GetTrueVSize());
        fields[p]->UseDevice(true);
        Snapshot(input / ("port" + std::to_string(p) + ".bin"), *fields[p], false);
      }
    }
  }

  bool OperatorOnly() const { return enabled && operator_only; }

  void Apply(const ComplexOperator &A)
  {
    MFEM_VERIFY(OperatorOnly(), "Not an operator-only probe!");
    Evaluate(A, "operator_only");
  }

  void Capture(int p, const ComplexVector &field, const ComplexOperator &A)
  {
    if (!enabled)
      return;
    MFEM_VERIFY(!operator_only && !fields.count(p), "Invalid/duplicate capture!");
    fields[p] = std::make_unique<ComplexVector>(field.Size());
    fields[p]->UseDevice(true);
    *fields[p] = field;
    Snapshot(output / ("port" + std::to_string(p) + ".bin"), *fields[p], true);
    if (fields.size() == ports.size())
      Evaluate(A, "capture");
  }
};

}  // namespace palace
#endif
