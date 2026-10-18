// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_UTILS_FIELDCOMPARISON_HPP
#define PALACE_UTILS_FIELDCOMPARISON_HPP

#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <limits>
#include <map>
#include <string>
#include <vector>
#include "fem/gridfunction.hpp"
#include "models/domainpostoperator.hpp"
#include "utils/communication.hpp"
#include "utils/timer.hpp"

namespace palace
{

// Single-rank, identical-mesh diagnostic. Python binds files to mesh/config/dependency
// hashes before mounting a reference. File layout: 8-byte magic, uint64 size, then
// real and imaginary IEEE754 doubles in native order (the local x86-64 runner).
inline void FieldSnapshot(const std::filesystem::path &path, GridFunction &field, bool save)
{
  const std::array<char, 8> magic{'P', 'A', 'L', 'F', '6', '4', 'V', '1'};
  const std::uint64_t count = field.Real().Size();
  MFEM_VERIFY(field.HasImag() && field.Imag().Size() == field.Real().Size(),
              "Field snapshot needs a complex field!");
  if (save)
  {
    std::filesystem::create_directories(path.parent_path());
    const auto temporary = path.string() + ".tmp";
    std::ofstream out(temporary, std::ios::binary | std::ios::trunc);
    out.write(magic.data(), magic.size());
    out.write(reinterpret_cast<const char *>(&count), sizeof(count));
    out.write(reinterpret_cast<const char *>(field.Real().HostRead()), count * sizeof(double));
    out.write(reinterpret_cast<const char *>(field.Imag().HostRead()), count * sizeof(double));
    out.close();
    MFEM_VERIFY(out, "Failed to save field snapshot!");
    std::filesystem::rename(temporary, path);
  }
  else
  {
    MFEM_VERIFY(std::filesystem::file_size(path) == magic.size() + sizeof(count) +
                                                     2 * count * sizeof(double),
                "Field snapshot size differs from current FE space!");
    std::ifstream in(path, std::ios::binary);
    std::array<char, 8> found{};
    std::uint64_t found_count = 0;
    in.read(found.data(), found.size());
    in.read(reinterpret_cast<char *>(&found_count), sizeof(found_count));
    MFEM_VERIFY(found == magic && found_count == count, "Invalid field snapshot header!");
    in.read(reinterpret_cast<char *>(field.Real().HostWrite()), count * sizeof(double));
    in.read(reinterpret_cast<char *>(field.Imag().HostWrite()), count * sizeof(double));
    MFEM_VERIFY(in, "Failed to read field snapshot!");
  }
}

inline void CompareFieldSnapshots(GridFunction &E, GridFunction &B,
                                   const DomainPostOperator &mass,
                                   const std::vector<int> &regions, int excitation,
                                   std::size_t frequency_index, const char *save_dir,
                                   const char *reference_dir)
{
  MFEM_VERIFY(Mpi::Size(E.GetComm()) == 1, "Field snapshots are single-rank only!");
  const auto started = Timer::Now();
  const std::string stem = "s" + std::to_string(excitation) + "-f" +
                           std::to_string(frequency_index);
  if (save_dir)
  {
    FieldSnapshot(std::filesystem::path(save_dir) / (stem + "-E.bin"), E, true);
    FieldSnapshot(std::filesystem::path(save_dir) / (stem + "-B.bin"), B, true);
  }
  if (reference_dir)
  {
    GridFunction ref_E(*E.ParFESpace(), true), ref_B(*B.ParFESpace(), true);
    FieldSnapshot(std::filesystem::path(reference_dir) / (stem + "-E.bin"), ref_E, false);
    FieldSnapshot(std::filesystem::path(reference_dir) / (stem + "-B.bin"), ref_B, false);
    auto energy = [&](int idx)
    {
      return idx < 0 ? std::array<double, 2>{mass.GetElectricFieldEnergy(ref_E),
                                           mass.GetMagneticFieldEnergy(ref_B)} :
                       std::array<double, 2>{mass.GetDomainElectricFieldEnergy(idx, ref_E),
                                             mass.GetDomainMagneticFieldEnergy(idx, ref_B)};
    };
    std::map<int, std::array<double, 2>> norms;
    norms.emplace(-1, energy(-1));
    for (int region : regions) norms.emplace(region, energy(region));
    // Consume only the reference scratch fields; never modify the computed solution.
    ref_E.Real() -= E.Real();
    ref_E.Imag() -= E.Imag();
    ref_B.Real() -= B.Real();
    ref_B.Imag() -= B.Imag();
    for (const auto &[idx, reference] : norms)
    {
      const auto difference = energy(idx);
      std::array<double, 2> relative{};
      for (int i = 0; i < 2; i++)
      {
        MFEM_VERIFY(std::isfinite(reference[i]) && reference[i] >= 0.0 &&
                        std::isfinite(difference[i]) && difference[i] >= 0.0,
                    "Invalid field energy norm!");
        relative[i] = reference[i] > 0.0 ? std::sqrt(difference[i] / reference[i]) :
                      difference[i] == 0.0 ? 0.0 : std::numeric_limits<double>::infinity();
      }
      Mpi::Print(E.GetComm(),
                 "PALACE_FIELD_COMPARE: excitation={} frequency_index={} region={} "
                 "relative_E={:.12e} relative_B={:.12e}\n",
                 excitation, frequency_index, idx, relative[0], relative[1]);
    }
  }
  Mpi::Print(E.GetComm(), "PALACE_FIELD_SNAPSHOT: excitation={} frequency_index={} seconds={:.6f}\n",
             excitation, frequency_index, Timer::Duration(Timer::Now() - started).count());
}

}  // namespace palace

#endif
