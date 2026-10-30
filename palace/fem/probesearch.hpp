// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_FEM_PROBESEARCH_HPP
#define PALACE_FEM_PROBESEARCH_HPP

// Host-only candidate selection. Workers never access MFEM, CUDA or its allocators.
#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>
#if defined(_OPENMP)
#include <omp.h>
#endif

namespace palace::fem::probe
{
inline constexpr int CandidateCap = 128;
using Candidate = std::pair<double, int>;  // Distance, then element ID breaks ties.
using Coordinates = std::array<double, 3>;
using CandidateHeap = std::priority_queue<Candidate>;

inline int RequestedThreads()
{
  const char *option = std::getenv("PALACE_PROBE_THREADS");
  if (!option)
  {
    return 1;
  }
  const std::string_view value(option);
  int threads = 0;
  const auto parsed = std::from_chars(value.data(), value.data() + value.size(), threads);
  if (parsed.ec != std::errc{} || parsed.ptr != value.data() + value.size() ||
      threads < 1 || threads > 64)
  {
    throw std::invalid_argument("PALACE_PROBE_THREADS must be an integer in 1..64");
  }
#if !defined(_OPENMP)
  if (threads != 1)
  {
    throw std::invalid_argument("PALACE_PROBE_THREADS > 1 requires an OpenMP build");
  }
#endif
  return threads;
}

struct NearestCenters
{
  std::vector<CandidateHeap> candidates;
  int threads_used = 0;
};

inline NearestCenters FindNearestCenters(const std::vector<Coordinates> &centers,
                                         const std::vector<Coordinates> &points,
                                         int threads)
{
  if (threads < 1 || threads > 64 || centers.size() > std::numeric_limits<int>::max() ||
      points.size() > std::numeric_limits<int>::max())
  {
    throw std::invalid_argument("Invalid probe search size or thread count");
  }
#if !defined(_OPENMP)
  if (threads != 1)
  {
    throw std::invalid_argument("Parallel probe search requires an OpenMP build");
  }
#endif
  NearestCenters result;
  result.candidates.reserve(points.size());
  for (std::size_t i = 0; i < points.size(); i++)
  {
    std::vector<Candidate> storage;
    storage.reserve(std::min<std::size_t>(CandidateCap, centers.size()));
    result.candidates.emplace_back(std::less<Candidate>{}, std::move(storage));
  }
  if (centers.empty() || points.empty())
  {
    return result;
  }
  std::vector<unsigned char> valid(centers.size());
  for (std::size_t e = 0; e < centers.size(); e++)
  {
    valid[e] = std::all_of(centers[e].begin(), centers[e].end(),
                           [](double x) { return std::isfinite(x); });
  }
  const int count = static_cast<int>(points.size());
  const auto search = [&](int m)
  {
    const auto &point = points[m];
    if (!std::all_of(point.begin(), point.end(), [](double x) { return std::isfinite(x); }))
    {
      return;
    }
    auto &heap = result.candidates[m];  // One query/heap per worker; capacity preallocated.
    for (int e = 0; e < static_cast<int>(centers.size()); e++)
    {
      if (!valid[e])
      {
        continue;
      }
      double distance = 0.0;
      for (int d = 0; d < 3; d++)
      {
        const double delta = centers[e][d] - point[d];
        distance += delta * delta;
      }
      const Candidate candidate{std::sqrt(distance), e};
      if (heap.size() < CandidateCap)
      {
        heap.push(candidate);
      }
      else if (candidate < heap.top())
      {
        heap.pop();
        heap.push(candidate);
      }
    }
  };
#if defined(_OPENMP)
  const int workers = std::min(threads, count);
#pragma omp parallel num_threads(workers)
  {
#pragma omp single
    result.threads_used = omp_get_num_threads();
#pragma omp for schedule(static)
    for (int m = 0; m < count; m++)
    {
      search(m);
    }
  }
#else
  result.threads_used = 1;
  for (int m = 0; m < count; m++)
  {
    search(m);
  }
#endif
  return result;
}
}  // namespace palace::fem::probe
#endif
