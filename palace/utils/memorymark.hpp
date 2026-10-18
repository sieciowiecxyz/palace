// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_UTILS_MEMORYMARK_HPP
#define PALACE_UTILS_MEMORYMARK_HPP

// Optional accounting hook supplied by the local CUDA adapter. No dependency or
// device synchronization when absent. Labels passed here are fixed literals.
extern "C" void PalaceMemoryMark(const char *) __attribute__((weak));

namespace palace
{
inline void MemoryMark(const char *label)
{
  if (PalaceMemoryMark) PalaceMemoryMark(label);
}
}
#endif
