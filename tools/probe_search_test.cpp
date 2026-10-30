// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Standalone CPU test: no MFEM, CUDA, simulation or external test dependencies.
#include <chrono>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include "fem/probesearch.hpp"

namespace probe = palace::fem::probe;
int checks = 0;
void Check(bool condition, const char *message)
{
  checks++;
  if (!condition)
  {
    throw std::runtime_error(message);
  }
}

std::vector<probe::Candidate> Sorted(probe::CandidateHeap heap)
{
  std::vector<probe::Candidate> result;
  while (!heap.empty())
  {
    result.push_back(heap.top());
    heap.pop();
  }
  std::reverse(result.begin(), result.end());
  return result;
}

std::vector<probe::Candidate> Oracle(const std::vector<probe::Coordinates> &centers,
                                     const probe::Coordinates &point)
{
  std::vector<probe::Candidate> all;
  for (int e = 0; e < static_cast<int>(centers.size()); e++)
  {
    const auto &c = centers[e];
    if (!std::isfinite(c[0]) || !std::isfinite(c[1]) || !std::isfinite(c[2]))
    {
      continue;
    }
    const double x = c[0] - point[0], y = c[1] - point[1], z = c[2] - point[2];
    all.emplace_back(std::sqrt(x * x + y * y + z * z), e);
  }
  std::sort(all.begin(), all.end());
  if (all.size() > probe::CandidateCap)
  {
    all.resize(probe::CandidateCap);
  }
  return all;
}

void Tests()
{
  std::mt19937 random(12345);
  std::uniform_real_distribution<double> value(-10.0, 10.0);
  std::vector<probe::Coordinates> centers(1003), points(23);
  for (auto &center : centers)
  {
    center = {value(random), value(random), value(random)};
  }
  centers[1] = centers[0];  // Ties must retain element-ID ordering.
  centers[2][1] = std::numeric_limits<double>::quiet_NaN();
  for (auto &point : points)
  {
    point = {value(random), value(random), value(random)};
  }
#if defined(_OPENMP)
  omp_set_dynamic(0);
  omp_set_num_threads(1);  // MFEM/global setting remains serial.
  const std::vector<int> counts{1, 2, 4, 8};
#else
  const std::vector<int> counts{1};
#endif
  std::vector<std::vector<probe::Candidate>> serial;
  for (const int threads : counts)
  {
    const auto result = probe::FindNearestCenters(centers, points, threads);
    Check(result.threads_used == threads, "Requested OpenMP team was not observed");
#if defined(_OPENMP)
    Check(omp_get_max_threads() == 1, "Probe search changed the global OpenMP setting");
#endif
    for (std::size_t q = 0; q < points.size(); q++)
    {
      const auto actual = Sorted(result.candidates[q]),
                 reference = Oracle(centers, points[q]);
      Check(actual.size() == reference.size(), "Wrong top-K size");
      for (std::size_t j = 0; j < actual.size(); j++)
      {
        Check(actual[j].second == reference[j].second,
              "Top-K element differs from full-sort oracle");
        Check(std::abs(actual[j].first - reference[j].first) <= 1e-12,
              "Top-K distance differs from full-sort oracle");
      }
      if (threads == 1)
      {
        serial.push_back(actual);
      }
      else
      {
        Check(actual == serial[q], "Parallel result differs bitwise from serial result");
      }
    }
  }
  auto none = probe::FindNearestCenters({}, points, 1);
  Check(none.threads_used == 0 && none.candidates.size() == points.size(), "Empty centers");
  Check(probe::FindNearestCenters(centers, {}, 1).threads_used == 0, "Empty queries");
  auto ties = probe::FindNearestCenters(std::vector<probe::Coordinates>(140, {1, 0, 0}),
                                        {{0, 0, 0}}, counts.back());
  auto selected = Sorted(ties.candidates[0]);
  Check(selected.size() == 128 && selected.front().second == 0 &&
            selected.back().second == 127,
        "Tie/cap selection is not deterministic");
  Check(ties.threads_used == 1, "Threads should be capped by query count");
  auto small = probe::FindNearestCenters({{0, 0, 0}, {1, 0, 0}}, {{0, 0, 0}}, 1);
  Check(small.candidates[0].size() == 2, "NE below K");
  const double nan = std::numeric_limits<double>::quiet_NaN();
  Check(probe::FindNearestCenters(centers, {{nan, 0, 0}}, 1).candidates[0].empty(),
        "Nonfinite query must remain unresolved");
  const char *previous = std::getenv("PALACE_PROBE_THREADS");
  const bool had_previous = previous != nullptr;
  const std::string saved = previous ? previous : "";
  for (const char *bad : {"", "0", "-1", "65", "4x", "1.5", " 4", "9999999999999999"})
  {
    setenv("PALACE_PROBE_THREADS", bad, 1);
    bool rejected = false;
    try
    {
      (void)probe::RequestedThreads();
    }
    catch (const std::invalid_argument &)
    {
      rejected = true;
    }
    Check(rejected, "Invalid thread option accepted");
  }
  setenv("PALACE_PROBE_THREADS", "1", 1);
  Check(probe::RequestedThreads() == 1, "Serial option rejected");
#if !defined(_OPENMP)
  setenv("PALACE_PROBE_THREADS", "2", 1);
  bool rejected = false;
  try
  {
    (void)probe::RequestedThreads();
  }
  catch (const std::invalid_argument &)
  {
    rejected = true;
  }
  Check(rejected, "No-OpenMP build silently accepted parallel request");
#endif
  if (had_previous)
  {
    setenv("PALACE_PROBE_THREADS", saved.c_str(), 1);
  }
  else
  {
    unsetenv("PALACE_PROBE_THREADS");
  }
}

void Benchmark()
{
  // Same order of magnitude as the medium rescue, without MFEM/solver work.
  std::vector<probe::Coordinates> centers(1700660), points(23);
  std::mt19937 random(12345);
  std::uniform_real_distribution<double> value(-1.0, 1.0);
  for (auto &center : centers)
  {
    center = {value(random), value(random), value(random)};
  }
  for (auto &point : points)
  {
    point = {value(random), value(random), value(random)};
  }
  for (int threads : {1, 2, 4, 8})
  {
    for (int repetition = 0; repetition < 3; repetition++)
    {
      const auto start = std::chrono::steady_clock::now();
      const auto result = probe::FindNearestCenters(centers, points, threads);
      const double seconds =
          std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
      std::cout << "{\"threads_requested\":" << threads
                << ",\"threads_used\":" << result.threads_used
                << ",\"repetition\":" << repetition << ",\"selection_seconds\":" << seconds
                << "}\n";
    }
  }
}

int main(int argc, char *argv[])
{
  try
  {
    Tests();
    std::cout << "{\"tests_passed\":true,\"checks\":" << checks << "}\n";
    if (argc == 2 && std::string(argv[1]) == "--benchmark")
    {
      Benchmark();
    }
    return 0;
  }
  catch (const std::exception &error)
  {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
