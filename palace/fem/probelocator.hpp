// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_FEM_PROBELOCATOR_HPP
#define PALACE_FEM_PROBELOCATOR_HPP

// Internal opt-in probe search shared by the interpolator, diagnostics and tests.
// Do not include this implementation from the public InterpolationOperator header.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <ctime>
#include <queue>
#include <utility>
#include <vector>
#include <mfem.hpp>
#include "fem/probesearch.hpp"

namespace palace::fem::probe
{
struct Quality
{
  bool finite = true, strict = false, forward = false;
  double residual = 0.0, limit = 1.0e-12;
};

inline Quality CheckReference(mfem::Mesh &mesh, int element,
                              const mfem::IntegrationPoint &reference,
                              const mfem::Vector &point)
{
  Quality quality;
  quality.strict =
      mfem::Geometry::CheckPoint(mesh.GetElementBaseGeometry(element), reference, -1.0e-7);
  mfem::Vector mapped(point.Size());
  mesh.GetElementTransformation(element)->Transform(reference, mapped);
  double scale = 1.0;
  for (int d = 0; d < point.Size(); d++)
  {
    quality.finite = quality.finite && std::isfinite(mapped(d)) && std::isfinite(point(d));
    quality.residual = std::max(quality.residual, std::abs(mapped(d) - point(d)));
    scale = std::max(scale, std::abs(point(d)));
  }
  quality.limit *= scale;
  quality.forward = quality.finite && quality.residual <= quality.limit;
  return quality;
}

// Optional bounded evidence; production passes nullptr and emits aggregate counts only.
struct Trial
{
  int element, status;
  double distance;
  mfem::IntegrationPoint reference{};
  Quality quality;
};
struct Trace
{
  int point;
  std::vector<Candidate> candidates;
  std::vector<Trial> tried;
};
struct Statistics
{
  int initial_found = 0, rescued = 0, tried = 0, remaining = 0;
  int center_evaluations = 0;
  int selection_threads = 1;
  std::size_t snapshot_bytes = 0;
  double selection_wall_s = 0.0, selection_cpu_s = 0.0;
  double inverse_wall_s = 0.0, inverse_cpu_s = 0.0;
};

inline Statistics Rescue(mfem::Mesh &mesh, const mfem::DenseMatrix &points,
                         mfem::Array<int> &elements,
                         mfem::Array<mfem::IntegrationPoint> &references,
                         std::vector<Trace> *trace = nullptr, int threads = 1)
{
  MFEM_VERIFY(points.Height() == mesh.SpaceDimension() &&
                  elements.Size() == points.Width() && references.Size() == points.Width(),
              "Invalid probe search arrays");
  Statistics statistics;
  std::vector<int> missing;
  for (int i = 0; i < points.Width(); i++)
  {
    if (elements[i] < 0)
    {
      missing.push_back(i);
    }
  }
  statistics.initial_found = points.Width() - static_cast<int>(missing.size());
  statistics.remaining = static_cast<int>(missing.size());
  if (trace)
  {
    trace->clear();
  }
  if (missing.empty())
  {
    return statistics;
  }
  using Clock = std::chrono::steady_clock;
  auto wall = Clock::now();
  auto cpu = std::clock();
  std::vector<CandidateHeap> nearest(missing.size());
  if (threads > 1)
  {
    MFEM_VERIFY(points.Height() > 0 && points.Height() <= 3,
                "Parallel probe search requires at most three coordinates");
    // Extract geometry serially: MFEM transformations and memory pools are shared.
    std::vector<Coordinates> centers(mesh.GetNE()), queries(missing.size());
    mfem::Vector center(points.Height());
    for (int e = 0; e < mesh.GetNE(); e++)
    {
      mesh.GetElementCenter(e, center);
      for (int d = 0; d < center.Size(); d++)
      {
        centers[e][d] = center(d);
      }
    }
    for (std::size_t m = 0; m < missing.size(); m++)
    {
      for (int d = 0; d < points.Height(); d++)
      {
        queries[m][d] = points(d, missing[m]);
      }
    }
    auto selected = FindNearestCenters(centers, queries, threads);
    nearest = std::move(selected.candidates);
    statistics.selection_threads = selected.threads_used;
    statistics.snapshot_bytes = (centers.size() + queries.size()) * sizeof(Coordinates);
  }
  else
  {
    mfem::Vector center(points.Height());
    for (int element = 0; element < mesh.GetNE(); element++)
    {
      mesh.GetElementCenter(element, center);
      bool finite = true;
      for (int d = 0; d < center.Size(); d++)
      {
        finite = finite && std::isfinite(center(d));
      }
      if (!finite)
      {
        continue;  // Never accept an invalid map; unresolved probes retain fallback.
      }
      for (std::size_t m = 0; m < missing.size(); m++)
      {
        double distance = 0.0;
        for (int d = 0; d < center.Size(); d++)
        {
          const double delta = center(d) - points(d, missing[m]);
          distance += delta * delta;
        }
        const Candidate candidate{std::sqrt(distance), element};
        auto &heap = nearest[m];
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
    }
  }
  statistics.center_evaluations = mesh.GetNE();
  statistics.selection_wall_s = std::chrono::duration<double>(Clock::now() - wall).count();
  statistics.selection_cpu_s = double(std::clock() - cpu) / CLOCKS_PER_SEC;
  wall = Clock::now();
  cpu = std::clock();
  mfem::InverseElementTransformation inverse;
  inverse.SetInitialGuessType(mfem::InverseElementTransformation::Center);
  inverse.SetSolverType(mfem::InverseElementTransformation::NewtonElementProject);
  inverse.SetReferenceTol(1.0e-15);
  inverse.SetPhysicalRelTol(4.0e-15);
  inverse.SetElementTol(1.0e-8);
  inverse.SetMaxIter(16);
  inverse.SetInitGuessPointsType(mfem::Quadrature1D::OpenHalfUniform);
  inverse.SetInitGuessRelOrder(-1);
  mfem::Vector point(points.Height());
  for (std::size_t m = 0; m < missing.size(); m++)
  {
    Trace evidence;
    evidence.point = missing[m];
    while (!nearest[m].empty())
    {
      evidence.candidates.push_back(nearest[m].top());
      nearest[m].pop();
    }
    std::sort(evidence.candidates.begin(), evidence.candidates.end());
    for (int d = 0; d < point.Size(); d++)
    {
      point(d) = points(d, evidence.point);
    }
    for (const auto &[distance, element] : evidence.candidates)
    {
      inverse.SetTransformation(*mesh.GetElementTransformation(element));
      mfem::IntegrationPoint reference{};
      const int status = inverse.Transform(point, reference);
      statistics.tried++;
      Trial trial{element, status, distance};
      if (status == mfem::InverseElementTransformation::Inside)
      {
        trial.reference = reference;
        trial.quality = CheckReference(mesh, element, reference, point);
      }
      const bool accepted = status == mfem::InverseElementTransformation::Inside &&
                            trial.quality.strict && trial.quality.forward;
      if (trace)
      {
        evidence.tried.push_back(trial);
      }
      if (accepted)
      {
        elements[evidence.point] = element;
        references[evidence.point] = reference;
        statistics.rescued++;
        statistics.remaining--;
        break;
      }
    }
    if (trace)
    {
      trace->push_back(std::move(evidence));
    }
  }
  statistics.inverse_wall_s = std::chrono::duration<double>(Clock::now() - wall).count();
  statistics.inverse_cpu_s = double(std::clock() - cpu) / CLOCKS_PER_SEC;
  return statistics;
}
}  // namespace palace::fem::probe
#endif  // PALACE_FEM_PROBELOCATOR_HPP
