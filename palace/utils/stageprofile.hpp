// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_UTILS_STAGEPROFILE_HPP
#define PALACE_UTILS_STAGEPROFILE_HPP

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <cstring>

namespace palace
{
// Host-only, inclusive phase measurements. Never synchronizes CUDA or changes timers.
class StageProfile
{
private:
  static bool Enabled()
  {
    static const bool enabled = []
    {
      const char *value = std::getenv("PALACE_STAGE_TRACE");
      return value && std::strcmp(value, "1") == 0;
    }();
    return enabled;
  }
  using Clock = std::chrono::steady_clock;
  const char *name;
  bool enabled;
  Clock::time_point start;
  std::clock_t cpu_start;

public:
  // Names are fixed internal labels, not user-provided text.
  explicit StageProfile(const char *label) : name(label), enabled(Enabled())
  {
    if (enabled)
    {
      start = Clock::now();
      cpu_start = std::clock();
      std::fprintf(stderr, "PALACE_STAGE_PROFILE {\"event\":\"begin\",\"name\":\"%s\",\"t_ns\":%lld}\n",
                   name, static_cast<long long>(std::chrono::duration_cast<std::chrono::nanoseconds>(start.time_since_epoch()).count()));
    }
  }
  StageProfile(const StageProfile &) = delete;
  StageProfile &operator=(const StageProfile &) = delete;
  ~StageProfile()
  {
    if (enabled)
    {
      const auto end = Clock::now();
      const auto cpu_end = std::clock();
      const double cpu_seconds = (cpu_start == std::clock_t(-1) || cpu_end == std::clock_t(-1))
          ? -1.0 : double(cpu_end - cpu_start) / CLOCKS_PER_SEC;
      std::fprintf(stderr, "PALACE_STAGE_PROFILE {\"event\":\"end\",\"name\":\"%s\",\"t_ns\":%lld,\"wall_s\":%.9f,\"process_cpu_s\":%.9f}\n",
                   name, static_cast<long long>(std::chrono::duration_cast<std::chrono::nanoseconds>(end.time_since_epoch()).count()),
                   std::chrono::duration<double>(end - start).count(), cpu_seconds);
    }
  }
};
}  // namespace palace
#endif
