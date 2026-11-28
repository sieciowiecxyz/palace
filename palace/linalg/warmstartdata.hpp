// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_LINALG_WARMSTARTDATA_HPP
#define PALACE_LINALG_WARMSTARTDATA_HPP

#include <filesystem>
#include <span>
#include <string>

namespace palace
{

class ComplexVector;
class FiniteElementSpace;

// Return a lowercase SHA-256 identifying the supported fine space and essential true DOFs.
// Throws for unsupported spaces.
std::string WarmStartSpaceId(FiniteElementSpace &space, std::span<const int> essential);

// The caller supplies physical residual norms for the final field and the initial guess.
// Publish a qualified sample atomically. An identical sample at the same sweep index is
// a no-op.
void WriteWarmStartSample(const std::filesystem::path &directory,
                          const std::string &space_id, int frequency_index, double omega,
                          int excitation, double rhs_norm, double initial_residual,
                          double residual_norm, double epsilon, const ComplexVector &field);

}  // namespace palace

#endif
