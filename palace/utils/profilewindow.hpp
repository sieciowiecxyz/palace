// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_UTILS_PROFILEWINDOW_HPP
#define PALACE_UTILS_PROFILEWINDOW_HPP
#include <chrono>
#include <cstdio>

// Adapter sync is diagnostic-only; no new CUDA dependency for ordinary runs.
extern "C" void PalaceProfileSynchronize() __attribute__((weak));

namespace palace
{
inline void ProfileHostRange(const char *event, const char *name)
{
  const auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                      std::chrono::steady_clock::now().time_since_epoch()).count();
  std::fprintf(stderr, "PALACE_PROFILE_RANGE {\"event\":\"%s\",\"name\":\"%s\",\"t_ns\":%lld}\n",
               event, name, static_cast<long long>(ns));
}
// Unwind the single-rank diagnostic solve before any incomplete RF postprocessing.
struct KrylovProfileComplete {};
}
#endif
