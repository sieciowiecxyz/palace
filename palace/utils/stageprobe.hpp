// SPDX-License-Identifier: Apache-2.0
#ifndef PALACE_UTILS_STAGEPROBE_HPP
#define PALACE_UTILS_STAGEPROBE_HPP

#include <cstdlib>
#include <stdexcept>
#include <string_view>

namespace palace
{
// Explicit diagnostic exits never represent a completed solve or RF result.
enum class StageProbe { None, Preprocess, Operators };

inline StageProbe RequestedStageProbe()
{
  const char *value = std::getenv("PALACE_STAGE_STOP");
  if (!value)
  {
    return StageProbe::None;
  }
  const std::string_view requested(value);
  if (requested == "preprocess")
  {
    return StageProbe::Preprocess;
  }
  if (requested == "operators")
  {
    return StageProbe::Operators;
  }
  throw std::invalid_argument("PALACE_STAGE_STOP must be preprocess or operators");
}

struct StageProbeComplete
{
  StageProbe stage;
};
}  // namespace palace
#endif
