// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_UTILS_PROFILEWINDOW_HPP
#define PALACE_UTILS_PROFILEWINDOW_HPP

// Adapter sync is diagnostic-only; no new CUDA dependency for ordinary runs.
extern "C" void PalaceProfileSynchronize() __attribute__((weak));

namespace palace
{
// Unwind the single-rank diagnostic solve before any incomplete RF postprocessing.
struct KrylovProfileComplete {};
}
#endif
