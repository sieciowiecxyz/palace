// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <map>
#include <memory>
#include <random>
#include <stdexcept>
#include <string>
#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>
#include "fem/fespace.hpp"
#include "fem/gridfunction.hpp"
#include "fem/interpolator.hpp"
#include "fem/mesh.hpp"
#include "fem/probelocator.hpp"
#include "utils/communication.hpp"
#include "utils/units.hpp"

#if defined(MFEM_USE_GSLIB)
namespace palace
{
namespace
{
class LocatorEnvironment
{
  bool present;
  std::string previous;

public:
  LocatorEnvironment() : present(std::getenv("PALACE_PROBE_LOCATOR") != nullptr)
  {
    if (present)
    {
      previous = std::getenv("PALACE_PROBE_LOCATOR");
    }
  }
  ~LocatorEnvironment()
  {
    if (present)
    {
      setenv("PALACE_PROBE_LOCATOR", previous.c_str(), 1);
    }
    else
    {
      unsetenv("PALACE_PROBE_LOCATOR");
    }
  }
  void Set(const char *value) { setenv("PALACE_PROBE_LOCATOR", value, 1); }
};

class ProbeThreadsEnvironment
{
  bool present;
  std::string previous;

public:
  explicit ProbeThreadsEnvironment(int threads)
    : present(std::getenv("PALACE_PROBE_THREADS") != nullptr)
  {
    if (present)
    {
      previous = std::getenv("PALACE_PROBE_THREADS");
    }
    setenv("PALACE_PROBE_THREADS", std::to_string(threads).c_str(), 1);
  }
  ~ProbeThreadsEnvironment()
  {
    if (present)
    {
      setenv("PALACE_PROBE_THREADS", previous.c_str(), 1);
    }
    else
    {
      unsetenv("PALACE_PROBE_THREADS");
    }
  }
};

mfem::Mesh CurvedMesh(mfem::Element::Type element)
{
  auto mesh = mfem::Mesh::MakeCartesian3D(2, 2, 2, element);
  mesh.SetCurvature(2);
  mesh.Transform(
      [](const mfem::Vector &x, mfem::Vector &y)
      {
        y = x;
        y(0) += 0.04 * x(1) * x(2);
        y(1) += 0.03 * x(0) * x(0);
      });
  return mesh;
}

struct Sample
{
  int element;
  mfem::IntegrationPoint reference;
};

std::map<int, config::ProbeData> MakeProbes(mfem::ParMesh &mesh,
                                            const std::map<int, Sample> &samples)
{
  std::map<int, config::ProbeData> probes;
  mfem::Vector physical(3);
  for (const auto &[id, sample] : samples)
  {
    mesh.GetElementTransformation(sample.element)->Transform(sample.reference, physical);
    for (int d = 0; d < 3; d++)
    {
      probes[id].center[d] = physical(d);
    }
  }
  return probes;
}

void Randomize(GridFunction &field, unsigned seed)
{
  std::mt19937 generator(seed);
  std::uniform_real_distribution<double> distribution(-1.0, 1.0);
  auto *real = field.Real().HostWrite();
  auto *imag = field.Imag().HostWrite();
  for (int i = 0; i < field.Real().Size(); i++)
  {
    real[i] = distribution(generator);
    imag[i] = distribution(generator);
  }
}

void CheckValues(InterpolationOperator &candidate, InterpolationOperator &oracle,
                 GridFunction &field, const std::map<int, Sample> &samples)
{
  const auto actual = candidate.ProbeField(field);
  const auto expected = oracle.ProbeField(field);
  REQUIRE(actual.size() == expected.size());
  REQUIRE(actual.size() == samples.size() * field.VectorDim());
  mfem::Vector real, imag;
  std::size_t index = 0;
  for (const auto &[id, sample] : samples)
  {
    field.Real().GetVectorValue(sample.element, sample.reference, real);
    field.Imag().GetVectorValue(sample.element, sample.reference, imag);
    for (int d = 0; d < field.VectorDim(); d++, index++)
    {
      const std::complex<double> reference(real(d), imag(d));
      // Predeclared FP64 oracle/action gate, plus independent known-reference sample.
      const double tolerance = 1.0e-11 + 1.0e-10 * std::abs(reference);
      INFO("probe=" << id << " component=" << d);
      CHECK(std::abs(actual[index] - expected[index]) <= tolerance);
      CHECK(std::abs(actual[index] - reference) <= tolerance);
    }
  }
}

// A valid length:width=10 target tetra and nearby disconnected compact distractors.
// The query is generated from the target reference coordinates, never hand-clamped.
mfem::Mesh DistractorMesh(int distractors)
{
  mfem::Mesh mesh(3, 4 * (distractors + 1), distractors + 1, 0, 3);
  mesh.AddVertex(0.0, 0.0, 0.0);
  mesh.AddVertex(10.0, 0.0, 0.0);
  mesh.AddVertex(0.0, 1.0, 0.0);
  mesh.AddVertex(0.0, 0.0, 1.0);
  mesh.AddTet(0, 1, 2, 3, 2);
  for (int i = 0; i < distractors; i++)
  {
    const double x = 0.05 + 0.03 * (i % 4);
    const double y = 0.65 + 0.03 * ((i / 4) % 4);
    const double z = 0.65 + 0.03 * (i / 16);
    const int first = mesh.GetNV();
    mesh.AddVertex(x, y, z);
    mesh.AddVertex(x + 0.01, y, z);
    mesh.AddVertex(x, y + 0.01, z);
    mesh.AddVertex(x, y, z + 0.01);
    mesh.AddTet(first, first + 1, first + 2, first + 3, 1);
  }
  mesh.FinalizeTetMesh(1, 0, true);
  mesh.SetCurvature(2);
  mesh.Transform(
      [](const mfem::Vector &x, mfem::Vector &y)
      {
        y = x;
        y(1) += 0.001 * x(0) * x(0);
      });
  return mesh;
}

int TargetElement(mfem::Mesh &mesh)
{
  for (int e = 0; e < mesh.GetNE(); e++)
  {
    if (mesh.GetAttribute(e) == 2)
    {
      return e;
    }
  }
  throw std::runtime_error("Missing known target element in test fixture");
}

mfem::DenseMatrix PhysicalPoint(mfem::Mesh &mesh, int element,
                                const mfem::IntegrationPoint &reference)
{
  mfem::Vector point(mesh.SpaceDimension());
  mesh.GetElementTransformation(element)->Transform(reference, point);
  mfem::DenseMatrix points(mesh.SpaceDimension(), 1);
  for (int d = 0; d < point.Size(); d++)
  {
    points(d, 0) = point(d);
  }
  return points;
}
}  // namespace

TEST_CASE("MFEM probe locator preserves curved complex H1 ND and RT fields",
          "[stage-probes][Serial]")
{
  REQUIRE(Mpi::Size(Mpi::World()) == 1);
  const auto element = GENERATE(mfem::Element::TETRAHEDRON, mfem::Element::HEXAHEDRON);
  const auto ordering = GENERATE(mfem::Ordering::byNODES, mfem::Ordering::byVDIM);
  const auto family = GENERATE(0, 1, 2, 3);  // ND, RT, H1 scalar, H1 vector
  LocatorEnvironment environment;
  auto serial = CurvedMesh(element);
  Mesh mesh(Mpi::World(), serial);
  mfem::ND_FECollection nd_collection(2, 3);
  FiniteElementSpace nd_space(mesh, &nd_collection);
  std::unique_ptr<mfem::FiniteElementCollection> collection;
  if (family == 0)
  {
    collection = std::make_unique<mfem::ND_FECollection>(2, 3);
  }
  else if (family == 1)
  {
    collection = std::make_unique<mfem::RT_FECollection>(1, 3);
  }
  else
  {
    collection = std::make_unique<mfem::H1_FECollection>(2, 3);
  }
  mfem::ParFiniteElementSpace space(&mesh.Get(), collection.get(), family == 3 ? 3 : 1,
                                    ordering);
  GridFunction field(space, true);
  mfem::IntegrationPoint ip;
  ip.Set3(0.173, 0.219, 0.137);
  std::map<int, Sample> samples{{41, {0, ip}}, {7, {3, ip}}, {109, {5, ip}}};
  const auto probes = MakeProbes(mesh.Get(), samples);
  Units units(1.0, 1.0);
  environment.Set("gslib");
  InterpolationOperator oracle(probes, units, nd_space);
  environment.Set("mfem");
  InterpolationOperator candidate(probes, units, nd_space);
  REQUIRE(candidate.UsesMFEMLocator());
  REQUIRE(candidate.GetProbes() == std::vector<int>{7, 41, 109});
  Randomize(field, 314159);
  CheckValues(candidate, oracle, field, samples);
  Randomize(field, 42);  // Geometry cache must not cache values/complex parts.
  CheckValues(candidate, oracle, field, samples);
  CHECK(candidate.UsesMFEMLocator());
}

TEST_CASE("MFEM probe locator keeps GSLIB ownership at boundaries and outside",
          "[stage-probes][Serial]")
{
  const auto element = GENERATE(mfem::Element::TETRAHEDRON, mfem::Element::HEXAHEDRON);
  const bool outside = GENERATE(false, true);
  LocatorEnvironment environment;
  auto serial = CurvedMesh(element);
  Mesh mesh(Mpi::World(), serial);
  mfem::ND_FECollection collection(2, 3);
  FiniteElementSpace space(mesh, &collection);
  GridFunction field(space, true);
  Randomize(field, 20261030);
  mfem::IntegrationPoint face, interior;
  face.Set3(0.0, 0.219, 0.137);
  interior.Set3(0.173, 0.219, 0.137);
  auto probes = MakeProbes(mesh.Get(), {{2, {0, face}}, {17, {3, interior}}});
  if (outside)
  {
    probes[2].center = {2.0, 2.0, 2.0};
  }
  Units units(1.0, 1.0);
  environment.Set("gslib");
  InterpolationOperator oracle(probes, units, space);
  environment.Set("mfem");
  InterpolationOperator candidate(probes, units, space);
  CHECK_FALSE(candidate.UsesMFEMLocator());
  const auto expected = oracle.ProbeField(field);
  const auto actual = candidate.ProbeField(field);
  REQUIRE(actual.size() == expected.size());
  for (std::size_t i = 0; i < actual.size(); i++)
  {
    CHECK(std::abs(actual[i] - expected[i]) <= 1.0e-12);
  }
  if (outside)
  {
    CHECK(actual[0] == std::complex<double>{});
    CHECK(actual[1] == std::complex<double>{});
    CHECK(actual[2] == std::complex<double>{});
  }
}

TEST_CASE("MFEM probe locator retains GSLIB for unsupported dimensions",
          "[stage-probes][Serial]")
{
  LocatorEnvironment environment;
  auto serial = mfem::Mesh::MakeCartesian2D(2, 2, mfem::Element::TRIANGLE, false);
  serial.SetCurvature(2);
  Mesh mesh(Mpi::World(), serial);
  mfem::ND_FECollection collection(2, 2);
  FiniteElementSpace space(mesh, &collection);
  GridFunction field(space, true);
  Randomize(field, 61);
  std::map<int, config::ProbeData> probes;
  probes[7].center = {0.173, 0.219, 0.0};
  environment.Set("gslib");
  InterpolationOperator oracle(probes, Units(1.0, 1.0), space);
  environment.Set("mfem");
  InterpolationOperator candidate(probes, Units(1.0, 1.0), space);
  CHECK_FALSE(candidate.UsesMFEMLocator());
  const auto expected = oracle.ProbeField(field);
  const auto actual = candidate.ProbeField(field);
  REQUIRE(actual.size() == expected.size());
  for (std::size_t i = 0; i < actual.size(); i++)
  {
    CHECK(std::abs(actual[i] - expected[i]) <= 1.0e-12);
  }
}

TEST_CASE("MFEM probe locator refuses stale geometry topology and foreign fields",
          "[stage-probes][Serial]")
{
  const int update = GENERATE(0, 1, 2);  // nodes, topology, foreign mesh
  LocatorEnvironment environment;
  environment.Set("mfem");
  auto serial = CurvedMesh(mfem::Element::TETRAHEDRON);
  Mesh mesh(Mpi::World(), serial);
  mfem::ND_FECollection collection(2, 3);
  FiniteElementSpace space(mesh, &collection);
  GridFunction field(space, true);
  mfem::IntegrationPoint ip;
  ip.Set3(0.173, 0.219, 0.137);
  const auto probes = MakeProbes(mesh.Get(), {{7, {0, ip}}});
  InterpolationOperator candidate(probes, Units(1.0, 1.0), space);
  REQUIRE(candidate.UsesMFEMLocator());
  if (update == 0)
  {
    mesh.Get().Transform(
        [](const mfem::Vector &x, mfem::Vector &y)
        {
          y = x;
          y(0) += 0.01;
        });
    CHECK_THROWS_AS(candidate.ProbeField(field), std::logic_error);
    // Same topology, officially updated coordinates: recreate instead of stale reuse.
    InterpolationOperator rebuilt(probes, Units(1.0, 1.0), space);
    Randomize(field, 17);
    CHECK_FALSE(rebuilt.ProbeField(field).empty());
  }
  else if (update == 1)
  {
    mesh.Get().UniformRefinement();
    CHECK_THROWS_AS(candidate.ProbeField(field), std::logic_error);
  }
  else
  {
    Mesh foreign_mesh(Mpi::World(), serial);
    FiniteElementSpace foreign_space(foreign_mesh, &collection);
    GridFunction foreign_field(foreign_space, true);
    CHECK_THROWS_AS(candidate.ProbeField(foreign_field), std::logic_error);
  }
}

TEST_CASE("MFEM probe locator validates mode empty probes and unsupported field map",
          "[stage-probes][Serial]")
{
  LocatorEnvironment environment;
  auto serial = CurvedMesh(mfem::Element::HEXAHEDRON);
  Mesh mesh(Mpi::World(), serial);
  mfem::ND_FECollection collection(2, 3);
  FiniteElementSpace space(mesh, &collection);
  Units units(1.0, 1.0);
  environment.Set("typo");
  CHECK_THROWS_AS(InterpolationOperator({}, units, space), std::invalid_argument);
  environment.Set("mfem");
  InterpolationOperator empty({}, units, space);
  GridFunction field(space, true);
  CHECK(empty.GetProbes().empty());
  CHECK(empty.ProbeField(field).empty());
  mfem::IntegrationPoint ip;
  ip.Set3(0.173, 0.219, 0.137);
  const auto probes = MakeProbes(mesh.Get(), {{7, {0, ip}}});
  InterpolationOperator candidate(probes, units, space);
  REQUIRE(candidate.UsesMFEMLocator());
  mfem::L2_FECollection l2_collection(1, 3);
  mfem::ParFiniteElementSpace l2_space(&mesh.Get(), &l2_collection);
  GridFunction l2_field(l2_space, true);
  Randomize(l2_field, 29);
  environment.Set("gslib");
  InterpolationOperator oracle(probes, units, space);
  const auto expected = oracle.ProbeField(l2_field);
  const auto actual = candidate.ProbeField(l2_field);
  CHECK_FALSE(candidate.UsesMFEMLocator());
  REQUIRE(actual.size() == expected.size());
  for (std::size_t i = 0; i < actual.size(); i++)
  {
    CHECK(std::abs(actual[i] - expected[i]) <= 1.0e-12);
  }
}

TEST_CASE("Bounded probe rescue finds a curved elongated cell omitted by nearest neighbors",
          "[stage-probes][Serial]")
{
  auto mesh = DistractorMesh(1);
  const int target = TargetElement(mesh);
  mfem::IntegrationPoint reference;
  reference.Set3(0.01, 0.1, 0.1);
  auto points = PhysicalPoint(mesh, target, reference);
  mfem::Array<int> elements;
  mfem::Array<mfem::IntegrationPoint> references;
  REQUIRE(mesh.FindPoints(points, elements, references, false) == 0);
  std::vector<fem::probe::Trace> trace;
  const auto stats = fem::probe::Rescue(mesh, points, elements, references, &trace);
  CHECK(stats.initial_found == 0);
  CHECK(stats.rescued == 1);
  CHECK(stats.remaining == 0);
  CHECK(stats.center_evaluations == mesh.GetNE());
  CHECK(stats.tried == 2);
  REQUIRE(trace.size() == 1);
  REQUIRE(trace[0].candidates.size() == 2);  // NE < fixed K
  CHECK(trace[0].candidates[0].second != target);
  CHECK(trace[0].candidates[1].second == target);
  CHECK(elements[0] == target);
  CHECK(std::abs(references[0].x - reference.x) <= 1.0e-12);
  CHECK(std::abs(references[0].y - reference.y) <= 1.0e-12);
  CHECK(std::abs(references[0].z - reference.z) <= 1.0e-12);
}

TEST_CASE("Bounded probe rescue preserves GSLIB complex fields in the rescued cell",
          "[stage-probes][Serial]")
{
  const auto family = GENERATE(0, 1, 2, 3);  // ND, RT, H1 scalar, H1 vector
#if defined(_OPENMP)
  const auto threads = GENERATE(1, 2, 4, 8);
#else
  const int threads = 1;
#endif
  ProbeThreadsEnvironment thread_environment(threads);
  LocatorEnvironment environment;
  auto serial = DistractorMesh(1);
  Mesh mesh(Mpi::World(), serial);
  const int target = TargetElement(mesh.Get());
  mfem::ND_FECollection nd_collection(2, 3);
  FiniteElementSpace nd_space(mesh, &nd_collection);
  std::unique_ptr<mfem::FiniteElementCollection> collection;
  if (family == 0)
  {
    collection = std::make_unique<mfem::ND_FECollection>(2, 3);
  }
  else if (family == 1)
  {
    collection = std::make_unique<mfem::RT_FECollection>(1, 3);
  }
  else
  {
    collection = std::make_unique<mfem::H1_FECollection>(2, 3);
  }
  mfem::ParFiniteElementSpace space(&mesh.Get(), collection.get(), family == 3 ? 3 : 1);
  GridFunction field(space, true);
  Randomize(field, 271828);
  mfem::IntegrationPoint reference;
  reference.Set3(0.01, 0.1, 0.1);
  const std::map<int, Sample> samples{{7, {target, reference}}, {9, {target, reference}}};
  const auto probes = MakeProbes(mesh.Get(), samples);
  environment.Set("gslib");
  InterpolationOperator oracle(probes, Units(1.0, 1.0), nd_space);
  environment.Set("mfem");
  InterpolationOperator candidate(probes, Units(1.0, 1.0), nd_space);
  REQUIRE(candidate.UsesMFEMLocator());
  CheckValues(candidate, oracle, field, samples);
}

TEST_CASE("Bounded probe rescue respects its cap and retains whole batch GSLIB fallback",
          "[stage-probes][Serial]")
{
  LocatorEnvironment environment;
  auto serial = DistractorMesh(128);
  Mesh mesh(Mpi::World(), serial);
  const int target = TargetElement(mesh.Get());
  mfem::IntegrationPoint reference;
  reference.Set3(0.01, 0.1, 0.1);
  auto points = PhysicalPoint(mesh.Get(), target, reference);
  mfem::Array<int> elements;
  mfem::Array<mfem::IntegrationPoint> references;
  REQUIRE(mesh.Get().mfem::Mesh::FindPoints(points, elements, references, false) == 0);
  std::vector<fem::probe::Trace> trace;
  const auto stats = fem::probe::Rescue(mesh.Get(), points, elements, references, &trace);
  CHECK(stats.initial_found == 0);
  CHECK(stats.rescued == 0);
  CHECK(stats.remaining == 1);  // Unknown at K=128, never declared outside.
  CHECK(stats.tried == 128);
  CHECK(elements[0] == -1);
  REQUIRE(trace.size() == 1);
  REQUIRE(trace[0].candidates.size() == 128);
  CHECK(std::none_of(trace[0].candidates.begin(), trace[0].candidates.end(),
                     [target](const auto &candidate)
                     { return candidate.second == target; }));
  mfem::ND_FECollection collection(2, 3);
  FiniteElementSpace space(mesh, &collection);
  GridFunction field(space, true);
  Randomize(field, 161803);
  const std::map<int, Sample> samples{{7, {target, reference}}};
  const auto probes = MakeProbes(mesh.Get(), samples);
  environment.Set("gslib");
  InterpolationOperator oracle(probes, Units(1.0, 1.0), space);
  environment.Set("mfem");
  InterpolationOperator candidate(probes, Units(1.0, 1.0), space);
  REQUIRE_FALSE(candidate.UsesMFEMLocator());
  CheckValues(candidate, oracle, field, samples);
}

TEST_CASE("Bounded probe rescue orders ties and never accepts boundary or outside points",
          "[stage-probes][Serial]")
{
  // Two disconnected symmetric cells have exactly equal center distances.
  mfem::Mesh symmetric(3, 8, 2, 0, 3);
  for (const double sign : {1.0, -1.0})
  {
    const int first = symmetric.GetNV();
    symmetric.AddVertex(sign * 1.75, 0.0, 0.0);
    symmetric.AddVertex(sign * 2.75, 0.0, 0.0);
    symmetric.AddVertex(sign * 1.75, 1.0, 0.0);
    symmetric.AddVertex(sign * 1.75, 0.0, 1.0);
    symmetric.AddTet(first, first + 1, first + 2, first + 3);
  }
  symmetric.FinalizeTetMesh(1, 0, true);
  mfem::DenseMatrix point(3, 1);
  point(0, 0) = 0.0;
  point(1, 0) = point(2, 0) = 0.25;
  mfem::Array<int> elements(1);
  mfem::Array<mfem::IntegrationPoint> references(1);
  elements = -1;
  std::vector<fem::probe::Trace> trace;
  const auto tied = fem::probe::Rescue(symmetric, point, elements, references, &trace);
  REQUIRE(trace.size() == 1);
  REQUIRE(trace[0].candidates.size() == 2);
  CHECK(trace[0].candidates[0].first == trace[0].candidates[1].first);
  CHECK(trace[0].candidates[0].second == 0);
  CHECK(trace[0].candidates[1].second == 1);
  CHECK(tied.rescued == 0);
  CHECK(tied.remaining == 1);

  auto mesh = CurvedMesh(mfem::Element::HEXAHEDRON);
  mfem::IntegrationPoint boundary;
  boundary.Set3(0.0, 0.2, 0.3);
  point = PhysicalPoint(mesh, 0, boundary);
  elements = -1;  // Exercise the rescue guard even if the first locator found this face.
  const auto face = fem::probe::Rescue(mesh, point, elements, references, &trace);
  CHECK(face.rescued == 0);
  CHECK(face.remaining == 1);
  CHECK(elements[0] == -1);
  CHECK(std::any_of(trace[0].tried.begin(), trace[0].tried.end(),
                    [](const auto &trial)
                    {
                      return trial.status == mfem::InverseElementTransformation::Inside &&
                             !trial.quality.strict;
                    }));
}

TEST_CASE("Bounded probe rescue does no work when all original probes were found",
          "[stage-probes][Serial]")
{
  auto mesh = CurvedMesh(mfem::Element::HEXAHEDRON);
  mfem::IntegrationPoint reference;
  reference.Set3(0.173, 0.219, 0.137);
  auto points = PhysicalPoint(mesh, 0, reference);
  mfem::Array<int> elements;
  mfem::Array<mfem::IntegrationPoint> references;
  REQUIRE(mesh.FindPoints(points, elements, references, false) == 1);
  const int original_element = elements[0];
  const auto original_reference = references[0];
  const auto stats = fem::probe::Rescue(mesh, points, elements, references);
  CHECK(stats.initial_found == 1);
  CHECK(stats.rescued == 0);
  CHECK(stats.tried == 0);
  CHECK(stats.remaining == 0);
  CHECK(stats.center_evaluations == 0);
  CHECK(elements[0] == original_element);
  CHECK(references[0].x == original_reference.x);
  CHECK(references[0].y == original_reference.y);
  CHECK(references[0].z == original_reference.z);
}
}  // namespace palace
#endif
