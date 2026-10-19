// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>

namespace palace
{
// Requested bytes, not measured migrations or GPU residency. Thread-local, cumulative.
struct BasisPrefetchStats
{
  std::uint64_t calls = 0, bytes = 0;
};
BasisPrefetchStats GetBasisPrefetchStats();
}
