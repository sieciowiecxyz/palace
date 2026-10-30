// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <optional>
#include <string>
#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "utils/communication.hpp"
#include "utils/geodata.hpp"
#include "utils/iodata.hpp"

namespace palace
{
namespace
{
class DirectMeshEnvironment
{
private:
  std::optional<std::string> previous;

public:
  explicit DirectMeshEnvironment(bool enabled)
  {
    if (const char *value = std::getenv("PALACE_SINGLE_RANK_DIRECT_MESH"))
    {
      previous = value;
    }
    setenv("PALACE_SINGLE_RANK_DIRECT_MESH", enabled ? "1" : "0", 1);
  }
  ~DirectMeshEnvironment()
  {
    if (previous)
    {
      setenv("PALACE_SINGLE_RANK_DIRECT_MESH", previous->c_str(), 1);
    }
    else
    {
      unsetenv("PALACE_SINGLE_RANK_DIRECT_MESH");
    }
  }
};

void CheckPartitionGeometry(mfem::ParMesh &expected, mfem::ParMesh &actual,
                            const char *stage)
{
  using Catch::Matchers::WithinAbs;
  const bool expected_flags = mesh::CheckRefinementFlags(expected);
  const bool actual_flags = mesh::CheckRefinementFlags(actual);
  CAPTURE(stage, expected_flags, actual_flags);
  std::fprintf(stderr, "PALACE_PREPROCESS_FLAGS stage=%s baseline=%d direct=%d\n",
               stage, int(expected_flags), int(actual_flags));
  REQUIRE(actual.GetNE() == expected.GetNE());
  REQUIRE(actual.GetNBE() == expected.GetNBE());
  REQUIRE(actual.GetNV() == expected.GetNV());
  CHECK(actual.GetNEdges() == expected.GetNEdges());
  CHECK(actual.GetNFaces() == expected.GetNFaces());
  CHECK(actual.CheckElementOrientation(false) == 0);
  CHECK(actual.CheckBdrElementOrientation(false) == 0);
  CHECK(actual_flags == expected_flags);
  REQUIRE(actual.GetNodes());
  REQUIRE(expected.GetNodes());
  CHECK(dynamic_cast<mfem::ParGridFunction *>(actual.GetNodes()) != nullptr);
  REQUIRE(actual.GetNodes()->Size() == expected.GetNodes()->Size());
  CHECK(actual.GetNodes()->FESpace()->GetMaxElementOrder() == 2);
  CHECK(actual.GetNodes()->FESpace()->GetOrdering() ==
        expected.GetNodes()->FESpace()->GetOrdering());
  CHECK(std::string(actual.GetNodes()->FESpace()->FEColl()->Name()) ==
        expected.GetNodes()->FESpace()->FEColl()->Name());
  const auto *actual_nodes = actual.GetNodes()->HostRead();
  const auto *expected_nodes = expected.GetNodes()->HostRead();
  for (int i = 0; i < actual.GetNodes()->Size(); i++)
  {
    CHECK_THAT(actual_nodes[i], WithinAbs(expected_nodes[i], 1.0e-13));
  }
  REQUIRE(actual.attributes.Size() == expected.attributes.Size());
  REQUIRE(actual.bdr_attributes.Size() == expected.bdr_attributes.Size());
  for (int i = 0; i < actual.attributes.Size(); i++)
  {
    CHECK(actual.attributes[i] == expected.attributes[i]);
  }
  for (int i = 0; i < actual.bdr_attributes.Size(); i++)
  {
    CHECK(actual.bdr_attributes[i] == expected.bdr_attributes[i]);
  }

  for (int e = 0; e < actual.GetNE(); e++)
  {
    CHECK(actual.GetAttribute(e) == expected.GetAttribute(e));
    const auto *a = actual.GetElement(e);
    const auto *b = expected.GetElement(e);
    REQUIRE(a->GetGeometryType() == b->GetGeometryType());
    REQUIRE(a->GetNVertices() == b->GetNVertices());
    for (int j = 0; j < a->GetNVertices(); j++)
    {
      CHECK(a->GetVertices()[j] == b->GetVertices()[j]);
    }
    if (a->GetGeometryType() == mfem::Geometry::TETRAHEDRON)
    {
      CHECK(static_cast<const mfem::Tetrahedron *>(a)->GetRefinementFlag() ==
            static_cast<const mfem::Tetrahedron *>(b)->GetRefinementFlag());
    }
    auto *ta = actual.GetElementTransformation(e);
    auto *tb = expected.GetElementTransformation(e);
    const auto &rule = mfem::IntRules.Get(a->GetGeometryType(), 3);
    for (int j = 0; j < rule.GetNPoints(); j++)
    {
      const auto &ip = rule.IntPoint(j);
      mfem::Vector xa, xb;
      ta->Transform(ip, xa);
      tb->Transform(ip, xb);
      for (int k = 0; k < xa.Size(); k++)
      {
        CHECK_THAT(xa(k), WithinAbs(xb(k), 1.0e-13));
      }
      ta->SetIntPoint(&ip);
      tb->SetIntPoint(&ip);
      CHECK_THAT(ta->Weight(), WithinAbs(tb->Weight(), 1.0e-13));
    }
  }
  for (int e = 0; e < actual.GetNBE(); e++)
  {
    CHECK(actual.GetBdrAttribute(e) == expected.GetBdrAttribute(e));
    const auto *a = actual.GetBdrElement(e);
    const auto *b = expected.GetBdrElement(e);
    REQUIRE(a->GetNVertices() == b->GetNVertices());
    for (int j = 0; j < a->GetNVertices(); j++)
    {
      CHECK(a->GetVertices()[j] == b->GetVertices()[j]);
    }
  }
  mfem::ND_FECollection fec(2, actual.Dimension());
  mfem::ParFiniteElementSpace actual_nd(&actual, &fec), expected_nd(&expected, &fec);
  CHECK(actual_nd.GetTrueVSize() == expected_nd.GetTrueVSize());
  // Exercise lazy adjacency creation: the direct path did not request a dual graph.
  const auto &actual_adjacency = actual.ElementToElementTable();
  const auto &expected_adjacency = expected.ElementToElementTable();
  REQUIRE(actual_adjacency.Size() == expected_adjacency.Size());
  for (int e = 0; e < actual_adjacency.Size(); e++)
  {
    REQUIRE(actual_adjacency.RowSize(e) == expected_adjacency.RowSize(e));
    for (int i = 0; i < actual_adjacency.RowSize(e); i++)
    {
      CHECK(actual_adjacency.GetRow(e)[i] == expected_adjacency.GetRow(e)[i]);
    }
  }
  // Equal dimensions alone would miss a changed orientation/sign or curved geometry.
  mfem::ConstantCoefficient one(1.0);
  mfem::ParBilinearForm actual_form(&actual_nd), expected_form(&expected_nd);
  for (auto *form : {&actual_form, &expected_form})
  {
    form->AddDomainIntegrator(new mfem::CurlCurlIntegrator(one));
    form->AddDomainIntegrator(new mfem::VectorFEMassIntegrator(one));
    form->Assemble();
    form->Finalize();
  }
  mfem::Vector x(actual_nd.GetVSize()), ax(x.Size()), bx(x.Size());
  for (int i = 0; i < x.Size(); i++)
  {
    x(i) = std::sin(0.3 * i);
  }
  actual_form.SpMat().Mult(x, ax);
  expected_form.SpMat().Mult(x, bx);
  const double expected_norm = bx.Norml2();
  REQUIRE(expected_norm > 0.0);
  ax -= bx;
  CHECK_THAT(ax.Norml2() / expected_norm, WithinAbs(0.0, 1.0e-12));
}
}  // namespace

TEST_CASE("One-rank direct distribution preserves curved mesh and refinement",
          "[stage_preprocess][Serial]")
{
  REQUIRE(Mpi::Size(Mpi::World()) == 1);
  const auto type = GENERATE(mfem::Element::TETRAHEDRON, mfem::Element::HEXAHEDRON);
  auto original = mfem::Mesh::MakeCartesian3D(2, 2, 2, type);
  original.SetCurvature(2);
  original.Transform([](const mfem::Vector &x, mfem::Vector &y)
  {
    y = x;
    y(0) += 0.05 * x(1) * x(2);
    y(1) += 0.03 * x(0) * x(0);
  });
  for (int e = 0; e < original.GetNE(); e++)
  {
    original.SetAttribute(e, 1 + e % 2);
  }
  for (int e = 0; e < original.GetNBE(); e++)
  {
    original.SetBdrAttribute(e, 21 + e % 2);
  }
  original.SetAttributes();
  original.Finalize(true, false);
  IoData iodata(Units(1.0, 1.0));
  iodata.model.refinement.max_it = 0;
  iodata.model.refinement.nonconformal = false;
  std::unique_ptr<mfem::ParMesh> expected, actual;
  {
    DirectMeshEnvironment option(false);
    expected = mesh::Partition(iodata, std::make_unique<mfem::Mesh>(original),
                               Mpi::World());
  }
  {
    DirectMeshEnvironment option(true);
    actual = mesh::Partition(iodata, std::make_unique<mfem::Mesh>(original),
                             Mpi::World());
  }
  REQUIRE(mesh::CheckRefinementFlags(*expected));
  REQUIRE(mesh::CheckRefinementFlags(*actual));
  CheckPartitionGeometry(*expected, *actual, "partitioned");
  expected->UniformRefinement();
  actual->UniformRefinement();
  CheckPartitionGeometry(*expected, *actual, "uniform_refined");
  expected->Finalize(true, false);
  actual->Finalize(true, false);
  REQUIRE(mesh::CheckRefinementFlags(*expected));
  REQUIRE(mesh::CheckRefinementFlags(*actual));
  CheckPartitionGeometry(*expected, *actual, "refinalized");
}
}  // namespace palace
