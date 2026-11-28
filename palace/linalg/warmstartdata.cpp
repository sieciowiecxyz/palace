// SPDX-License-Identifier: Apache-2.0

#include "warmstartdata.hpp"

#include <algorithm>
#include <bit>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string_view>
#include <system_error>
#include <vector>
#include <unistd.h>
#include <openssl/sha.h>
#include <mfem.hpp>
#include <nlohmann/json.hpp>
#include "fem/fespace.hpp"
#include "linalg/vector.hpp"
#include "utils/communication.hpp"

namespace palace
{

namespace
{

constexpr int MaxTrueDofs = 16384;

void Require(bool valid, const char *message)
{
  if (!valid)
  {
    throw std::invalid_argument(message);
  }
}

// Encode integers and IEEE double bits as fixed-width little-endian words.
void AppendWord(std::string &bytes, std::uint64_t word)
{
  for (int shift = 0; shift < 64; shift += 8)
  {
    bytes.push_back(static_cast<char>((word >> shift) & 0xff));
  }
}

std::string Sha256(std::string_view bytes)
{
  unsigned char digest[SHA256_DIGEST_LENGTH];
  if (!SHA256(reinterpret_cast<const unsigned char *>(bytes.data()), bytes.size(), digest))
  {
    throw std::runtime_error("Cannot hash warm-start data");
  }
  constexpr char hex[] = "0123456789abcdef";
  std::string hash;
  hash.reserve(2 * sizeof(digest));
  for (const auto byte : digest)
  {
    hash += hex[byte >> 4];
    hash += hex[byte & 15];
  }
  return hash;
}

void AppendElement(std::string &bytes, const mfem::Element &element,
                   const mfem::ElementTransformation &transformation)
{
  const auto *map =
      dynamic_cast<const mfem::IsoparametricTransformation *>(&transformation);
  const int vertices = element.GetNVertices();
  Require(map && map->Order() == 1 && map->GetPointMat().Width() == vertices &&
              map->GetPointMat().Height() == 3,
          "Warm-start requires straight-sided first-order mesh geometry");
  AppendWord(bytes, element.GetGeometryType());
  AppendWord(bytes, element.GetAttribute());
  AppendWord(bytes, vertices);
  const auto &points = map->GetPointMat();
  for (int j = 0; j < vertices; ++j)
  {
    AppendWord(bytes, element.GetVertices()[j]);
    for (int d = 0; d < 3; ++d)
    {
      const double coordinate = points(d, j);
      Require(std::isfinite(coordinate), "Nonfinite warm-start mesh coordinate");
      AppendWord(bytes, std::bit_cast<std::uint64_t>(coordinate));
    }
  }
}

bool IsNorm(double value)
{
  return std::isfinite(value) && value >= 0.0;
}

// Keep the pending file in the destination directory so publication is one atomic link.
class PendingSample
{
public:
  explicit PendingSample(const std::filesystem::path &directory)
    : path((directory / ".warmstart-XXXXXX").string()), fd(mkstemp(path.data()))
  {
    Check(fd >= 0, "Cannot create pending warm-start sample");
  }

  PendingSample(const PendingSample &) = delete;
  PendingSample &operator=(const PendingSample &) = delete;

  ~PendingSample()
  {
    if (fd >= 0)
    {
      close(fd);
    }
    unlink(path.c_str());
  }

  void Publish(const std::filesystem::path &destination, std::string_view payload)
  {
    auto pending = payload;
    while (!pending.empty())
    {
      const auto written = write(fd, pending.data(), pending.size());
      if (written < 0 && errno == EINTR)
      {
        continue;
      }
      Check(written > 0, "Cannot write pending warm-start sample");
      pending.remove_prefix(written);
    }
    Check(fsync(fd) == 0, "Cannot sync pending warm-start sample");
    const int closed = close(fd);
    fd = -1;
    Check(closed == 0, "Cannot close pending warm-start sample");

    if (link(path.c_str(), destination.c_str()) == 0)
    {
      return;
    }
    Check(errno == EEXIST, "Cannot publish warm-start sample");
    if (!std::filesystem::is_regular_file(std::filesystem::symlink_status(destination)) ||
        std::filesystem::file_size(destination) != payload.size())
    {
      throw std::runtime_error("Conflicting warm-start sample at " + destination.string());
    }
    std::ifstream existing(destination, std::ios::binary);
    std::string prior(payload.size(), '\0');
    if (!existing.read(prior.data(), prior.size()) || prior != payload)
    {
      throw std::runtime_error("Conflicting warm-start sample at " + destination.string());
    }
  }

private:
  static void Check(bool ok, const char *message)
  {
    if (!ok)
    {
      throw std::system_error(errno, std::generic_category(), message);
    }
  }

  std::string path;
  int fd;
};

}  // namespace

std::string WarmStartSpaceId(FiniteElementSpace &space, std::span<const int> essential)
{
  auto &fes = space.Get();
  const auto &fec = space.GetFEColl();
  auto &mesh = space.GetParMesh();
  const int n = space.GetTrueVSize();
  Require(Mpi::Size(space.GetComm()) == 1 && !space.IsBroken() && mesh.Conforming() &&
              mesh.Dimension() == 3 && mesh.SpaceDimension() == 3 &&
              dynamic_cast<const mfem::ND_FECollection *>(&fec) && fec.GetOrder() == 1 &&
              !fes.IsVariableOrder() && fes.GetVDim() == 1 && n > 0 && n <= MaxTrueDofs &&
              fes.GetVSize() == n && space.GlobalTrueVSize() == n,
          "Warm-start requires a conforming single-rank 3D ND1 space with at most 16384 "
          "true DOFs");

  std::string bytes = "palace-warmstart-space-v1";
  bytes.push_back('\0');
  bytes += fec.Name();
  bytes.push_back('\0');
  AppendWord(bytes, n);
  AppendWord(bytes, fes.GetOrdering());
  AppendWord(bytes, mesh.GetNV());

  // A conforming single-rank ND1 space has one sign-free local-to-true index per
  // local DOF. The element-local signs are encoded separately in GetElementDofs.
  std::vector<bool> seen(n);
  for (int i = 0; i < n; ++i)
  {
    const int tdof = fes.GetLocalTDofNumber(i);
    Require(tdof >= 0 && tdof < n && !seen[tdof],
            "Unsupported warm-start local-to-true DOF map");
    seen[tdof] = true;
    AppendWord(bytes, tdof);
  }

  AppendWord(bytes, mesh.GetNE());
  mfem::Array<int> dofs;
  mfem::DofTransformation transform;
  for (int e = 0; e < mesh.GetNE(); ++e)
  {
    AppendElement(bytes, *mesh.GetElement(e), *mesh.GetElementTransformation(e));
    fes.GetElementDofs(e, dofs, transform);
    Require(transform.IsIdentity(), "Unsupported warm-start element DOF transformation");
    AppendWord(bytes, dofs.Size());
    for (const int dof : dofs)
    {
      AppendWord(bytes, dof);
    }
  }
  AppendWord(bytes, mesh.GetNBE());
  for (int e = 0; e < mesh.GetNBE(); ++e)
  {
    AppendElement(bytes, *mesh.GetBdrElement(e), *mesh.GetBdrElementTransformation(e));
  }

  // The ordering and repetition of entries in an essential mask do not affect the space.
  std::vector<int> mask(essential.begin(), essential.end());
  std::sort(mask.begin(), mask.end());
  mask.erase(std::unique(mask.begin(), mask.end()), mask.end());
  AppendWord(bytes, mask.size());
  for (const int i : mask)
  {
    Require(i >= 0 && i < n, "Warm-start essential true DOF out of range");
    AppendWord(bytes, i);
  }
  return Sha256(bytes);
}

void WriteWarmStartSample(const std::filesystem::path &directory,
                          const std::string &space_id, int frequency_index, double omega,
                          int excitation, double rhs_norm, double initial_residual,
                          double residual_norm, double epsilon, const ComplexVector &field)
{
  constexpr std::string_view hex = "0123456789abcdef";
  const int n = field.Size();
  Require(!directory.empty() && space_id.size() == 2 * SHA256_DIGEST_LENGTH &&
              space_id.find_first_not_of(hex) == std::string::npos && n > 0 &&
              n <= MaxTrueDofs && field.Imag().Size() == n && frequency_index >= 0 &&
              excitation >= 0 && std::isfinite(omega) && omega > 0.0,
          "Invalid warm-start sample metadata");
  Require(IsNorm(rhs_norm) && IsNorm(initial_residual) && IsNorm(residual_norm) &&
              IsNorm(epsilon) && residual_norm <= epsilon,
          "Warm-start sample requires finite norms and a qualified final residual");

  const auto *real = field.Real().HostRead();
  const auto *imag = field.Imag().HostRead();
  for (int i = 0; i < n; ++i)
  {
    Require(std::isfinite(real[i]) && std::isfinite(imag[i]),
            "Nonfinite warm-start sample field");
  }
  const nlohmann::json sample = {{"schema", "palace-warmstart-sample-v1"},
                                 {"space_id", space_id},
                                 {"n", n},
                                 {"omega", omega},
                                 {"excitation", excitation},
                                 {"rhs_norm", rhs_norm},
                                 {"initial_residual", initial_residual},
                                 {"residual_norm", residual_norm},
                                 {"epsilon", epsilon},
                                 {"field_real", std::span(real, n)},
                                 {"field_imag", std::span(imag, n)}};
  const std::string payload = sample.dump() + '\n';
  const auto filename = "sample-" + std::to_string(frequency_index) + "-" +
                        std::to_string(excitation) + "-" + Sha256(payload) + ".json";
  std::filesystem::create_directories(directory);
  PendingSample(directory).Publish(directory / filename, payload);
}

}  // namespace palace
