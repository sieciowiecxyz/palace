// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include <algorithm>
#include <chrono>
#include <cmath>
#include <ctime>
#include <filesystem>
#include <stdexcept>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <random>
#include <string>
#include <utility>
#include <catch2/catch_test_macros.hpp>
#include <mfem.hpp>
#include "utils/communication.hpp"

namespace
{
void CheckIntArrays(const mfem::Array<int> &a, const mfem::Array<int> &b)
{
  REQUIRE(a.Size() == b.Size());
  for (int i = 0; i < a.Size(); i++)
  {
    CHECK(a[i] == b[i]);
  }
}

void CheckAttributeNames(mfem::AttributeSets &a, mfem::AttributeSets &b)
{
  REQUIRE(a.GetAttributeSetNames() == b.GetAttributeSetNames());
  for (const auto &name : a.GetAttributeSetNames())
  {
    CheckIntArrays(a.GetAttributeSet(name), b.GetAttributeSet(name));
  }
}

void CheckElements(mfem::Mesh &a, mfem::Mesh &b, bool boundary)
{
  const int count = boundary ? a.GetNBE() : a.GetNE();
  for (int e = 0; e < count; e++)
  {
    const auto *ea = boundary ? a.GetBdrElement(e) : a.GetElement(e);
    const auto *eb = boundary ? b.GetBdrElement(e) : b.GetElement(e);
    REQUIRE(ea->GetGeometryType() == eb->GetGeometryType());
    REQUIRE(ea->GetNVertices() == eb->GetNVertices());
    CHECK(ea->GetAttribute() == eb->GetAttribute());
    for (int v = 0; v < ea->GetNVertices(); v++)
    {
      CHECK(ea->GetVertices()[v] == eb->GetVertices()[v]);
    }
    auto *ta = boundary ? a.GetBdrElementTransformation(e) : a.GetElementTransformation(e);
    auto *tb = boundary ? b.GetBdrElementTransformation(e) : b.GetElementTransformation(e);
    const auto &rule = mfem::IntRules.Get(ea->GetGeometryType(), 5);
    double volume_a = 0.0, volume_b = 0.0;
    for (int q = 0; q < rule.GetNPoints(); q++)
    {
      const auto &ip = rule.IntPoint(q);
      ta->SetIntPoint(&ip);
      tb->SetIntPoint(&ip);
      mfem::Vector xa, xb;
      ta->Transform(ip, xa);
      tb->Transform(ip, xb);
      REQUIRE(xa.Size() == xb.Size());
      for (int d = 0; d < xa.Size(); d++)
      {
        CHECK(xa(d) == xb(d));
      }
      const auto &ja = ta->Jacobian();
      const auto &jb = tb->Jacobian();
      REQUIRE(ja.Height() == jb.Height());
      REQUIRE(ja.Width() == jb.Width());
      for (int i = 0; i < ja.Height(); i++)
      {
        for (int j = 0; j < ja.Width(); j++)
        {
          CHECK(ja(i, j) == jb(i, j));
        }
      }
      if (!boundary)
      {
        CHECK(ja.Det() > 0.0);
        CHECK(jb.Det() > 0.0);
      }
      CHECK(ta->Weight() > 0.0);
      CHECK(ta->Weight() == tb->Weight());
      volume_a += ip.weight * ta->Weight();
      volume_b += ip.weight * tb->Weight();
    }
    CHECK(volume_a > 0.0);
    CHECK(volume_a == volume_b);
  }
}

// Full meshes use aggregate exact comparisons; never assemble full ND matrices here.
struct StructuralCounts
{
  long long vertex_values = 0, node_values = 0, elements = 0, boundaries = 0;
  long long vertex_ids = 0, nodal_dofs = 0, nodal_vdofs = 0, orientation_ids = 0;
};

void ExactBytes(const void *a, const void *b, std::size_t count, std::size_t width,
                const char *kind, long long entity)
{
  if (std::memcmp(a, b, count * width) == 0)
  {
    return;
  }
  for (std::size_t i = 0; i < count; i++)
  {
    if (std::memcmp(static_cast<const char *>(a) + i * width,
                    static_cast<const char *>(b) + i * width, width) != 0)
    {
      std::fprintf(stderr,
                   "PALACE_IO06_FIRST_DIFFERENCE {\"kind\":\"%s\",\"entity\":%lld,"
                   "\"index\":%zu,\"width\":%zu}\n", kind, entity, i, width);
      throw std::runtime_error("Exact full structural comparison failed");
    }
  }
}

void ExactArray(const mfem::Array<int> &a, const mfem::Array<int> &b,
                const char *kind, long long entity)
{
  if (a.Size() != b.Size())
  {
    std::fprintf(stderr,
                 "PALACE_IO06_FIRST_DIFFERENCE {\"kind\":\"%s\",\"entity\":%lld,"
                 "\"size_a\":%d,\"size_b\":%d}\n", kind, entity, a.Size(), b.Size());
    throw std::runtime_error("Full structural array dimensions differ");
  }
  ExactBytes(a.GetData(), b.GetData(), a.Size(), sizeof(int), kind, entity);
}

void CheckFullStructure(mfem::Mesh &a, mfem::Mesh &b)
{
  StructuralCounts checked;
  REQUIRE(a.Dimension() == 3);
  REQUIRE(a.SpaceDimension() == 3);
  REQUIRE(b.Dimension() == a.Dimension());
  REQUIRE(b.SpaceDimension() == a.SpaceDimension());
  REQUIRE(a.GetNV() == b.GetNV());
  REQUIRE(a.GetNE() == b.GetNE());
  REQUIRE(a.GetNBE() == b.GetNBE());
  REQUIRE(a.GetNodes());
  REQUIRE(b.GetNodes());
  auto &na = *a.GetNodes();
  auto &nb = *b.GetNodes();
  auto &fa = *na.FESpace();
  auto &fb = *nb.FESpace();
  REQUIRE(na.Size() == nb.Size());
  REQUIRE(fa.GetMaxElementOrder() == 2);
  REQUIRE(fb.GetMaxElementOrder() == 2);
  REQUIRE(fa.GetNDofs() == fb.GetNDofs());
  REQUIRE(fa.GetVDim() == fb.GetVDim());
  REQUIRE(fa.GetOrdering() == fb.GetOrdering());
  REQUIRE(std::string(fa.FEColl()->Name()) == fb.FEColl()->Name());
  for (int v = 0; v < a.GetNV(); v++)
  {
    ExactBytes(a.GetVertex(v), b.GetVertex(v), 3, sizeof(double), "vertex_bits", v);
    checked.vertex_values += 3;
  }
  ExactBytes(na.HostRead(), nb.HostRead(), na.Size(), sizeof(double), "node_bits", -1);
  checked.node_values = na.Size();
  CheckAttributeNames(a.attribute_sets, b.attribute_sets);
  CheckAttributeNames(a.bdr_attribute_sets, b.bdr_attribute_sets);
  ExactArray(a.attributes, b.attributes, "attributes", -1);
  ExactArray(a.bdr_attributes, b.bdr_attributes, "boundary_attributes", -1);
  mfem::Array<int> da, db, va, vb, oa, ob;
  for (bool boundary : {false, true})
  {
    const int count = boundary ? a.GetNBE() : a.GetNE();
    for (int e = 0; e < count; e++)
    {
      const auto *ea = boundary ? a.GetBdrElement(e) : a.GetElement(e);
      const auto *eb = boundary ? b.GetBdrElement(e) : b.GetElement(e);
      const int meta_a[] = {int(ea->GetGeometryType()), ea->GetNVertices(), ea->GetAttribute()};
      const int meta_b[] = {int(eb->GetGeometryType()), eb->GetNVertices(), eb->GetAttribute()};
      ExactBytes(meta_a, meta_b, 3, sizeof(int), boundary ? "bdr_metadata" : "metadata", e);
      ExactBytes(ea->GetVertices(), eb->GetVertices(), ea->GetNVertices(), sizeof(int),
                  boundary ? "bdr_vertex_ids" : "vertex_ids", e);
      checked.vertex_ids += ea->GetNVertices();
      if (boundary)
      {
        fa.GetBdrElementDofs(e, da); fb.GetBdrElementDofs(e, db);
        fa.GetBdrElementVDofs(e, va); fb.GetBdrElementVDofs(e, vb);
        checked.boundaries++;
      }
      else
      {
        fa.GetElementDofs(e, da); fb.GetElementDofs(e, db);
        fa.GetElementVDofs(e, va); fb.GetElementVDofs(e, vb);
        checked.elements++;
      }
      ExactArray(da, db, boundary ? "bdr_node_dofs" : "node_dofs", e);
      ExactArray(va, vb, boundary ? "bdr_node_vdofs" : "node_vdofs", e);
      checked.nodal_dofs += da.Size();
      checked.nodal_vdofs += va.Size();
      if (!boundary)
      {
        a.GetElementEdges(e, da, oa); b.GetElementEdges(e, db, ob);
        ExactArray(da, db, "element_edges", e);
        ExactArray(oa, ob, "edge_orientations", e);
        checked.orientation_ids += oa.Size();
        a.GetElementFaces(e, da, oa); b.GetElementFaces(e, db, ob);
        ExactArray(da, db, "element_faces", e);
        ExactArray(oa, ob, "face_orientations", e);
        checked.orientation_ids += oa.Size();
      }
      else
      {
        int face_a, face_b, orientation_a, orientation_b;
        a.GetBdrElementFace(e, &face_a, &orientation_a);
        b.GetBdrElementFace(e, &face_b, &orientation_b);
        const int ba[] = {face_a, orientation_a}, bb[] = {face_b, orientation_b};
        ExactBytes(ba, bb, 2, sizeof(int), "bdr_face_orientation", e);
        checked.orientation_ids++;
      }
    }
  }
  REQUIRE(a.GetNEdges() == b.GetNEdges());
  REQUIRE(a.GetNFaces() == b.GetNFaces());
  // Supplement the exhaustive coordinates/connectivity with fixed physical map samples.
  int samples = 0;
  for (bool boundary : {false, true})
  {
    const int count = boundary ? a.GetNBE() : a.GetNE();
    for (int e : {0, count / 7, count / 2, count - 1})
    {
      auto *ta = boundary ? a.GetBdrElementTransformation(e) : a.GetElementTransformation(e);
      auto *tb = boundary ? b.GetBdrElementTransformation(e) : b.GetElementTransformation(e);
      const auto geometry = boundary ? a.GetBdrElement(e)->GetGeometryType()
                                     : a.GetElement(e)->GetGeometryType();
      const auto &rule = mfem::IntRules.Get(geometry, 5);
      for (int q : {0, rule.GetNPoints() / 2, rule.GetNPoints() - 1})
      {
        const auto &ip = rule.IntPoint(q);
        ta->SetIntPoint(&ip); tb->SetIntPoint(&ip);
        mfem::Vector xa, xb;
        ta->Transform(ip, xa); tb->Transform(ip, xb);
        REQUIRE(xa.Size() == xb.Size());
        ExactBytes(xa.HostRead(), xb.HostRead(), xa.Size(), sizeof(double), "sample_map", e);
        const auto &ja = ta->Jacobian(); const auto &jb = tb->Jacobian();
        REQUIRE(ja.Height() == jb.Height());
        REQUIRE(ja.Width() == jb.Width());
        ExactBytes(ja.Data(), jb.Data(), ja.Height() * ja.Width(), sizeof(double),
                    "sample_jacobian", e);
        REQUIRE(ta->Weight() > 0.0);
        REQUIRE(ta->Weight() == tb->Weight());
        samples++;
      }
    }
  }
  std::fprintf(stderr,
               "PALACE_IO06_STRUCTURE {\"vertices\":%d,\"elements\":%lld,\"boundaries\":%lld,"
               "\"vertex_values\":%lld,\"node_values\":%lld,\"vertex_ids\":%lld,"
               "\"nodal_dofs\":%lld,\"nodal_vdofs\":%lld,\"orientation_ids\":%lld,"
               "\"physical_map_samples\":%d,\"all_bits_equal\":true,"
               "\"full_nd_operators_qualified\":false,\"rf_qualified\":false}\n",
               a.GetNV(), checked.elements, checked.boundaries, checked.vertex_values,
               checked.node_values, checked.vertex_ids, checked.nodal_dofs, checked.nodal_vdofs,
               checked.orientation_ids, samples);
}

std::unique_ptr<mfem::BilinearForm> Assemble(mfem::FiniteElementSpace &space,
                                           mfem::Coefficient &one, bool curl)
{
  auto form = std::make_unique<mfem::BilinearForm>(&space);
  if (curl)
  {
    form->AddDomainIntegrator(new mfem::CurlCurlIntegrator(one));
  }
  else
  {
    form->AddDomainIntegrator(new mfem::VectorFEMassIntegrator(one));
  }
  form->Assemble();
  form->Finalize();
  return form;
}
}  // namespace

TEST_CASE("Binary MSH2.2 preserves curved P2 native mesh and ND operators",
          "[stage_mesh_binary][Serial]")
{
  REQUIRE(palace::Mpi::Size(palace::Mpi::World()) == 1);
  const char *ascii = std::getenv("PALACE_IO06_ASCII");
  const char *binary = std::getenv("PALACE_IO06_BINARY");
  REQUIRE(ascii);
  REQUIRE(binary);
  const char *mode = std::getenv("PALACE_IO06_STRUCTURAL_ONLY");
  const bool structural_only = mode && std::string(mode) == "1";
  if ((mode && !structural_only) ||
      (!structural_only && (std::filesystem::file_size(ascii) > 4 * 1024 * 1024 ||
                            std::filesystem::file_size(binary) > 4 * 1024 * 1024)))
  {
    throw std::runtime_error("Large meshes require explicit PALACE_IO06_STRUCTURAL_ONLY=1; "
                             "full sparse ND assembly is forbidden");
  }
  auto load = [](const char *path, const char *kind)
  {
    const auto start = std::chrono::steady_clock::now();
    const auto cpu = std::clock();
    auto mesh = std::make_unique<mfem::Mesh>(std::string(path), 0, 0, true);
    std::fprintf(stderr, "PALACE_IO06_LOAD {\"kind\":\"%s\",\"wall_s\":%.17g,\"cpu_s\":%.17g}\n",
                 kind, std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count(),
                 double(std::clock() - cpu) / CLOCKS_PER_SEC);
    return mesh;
  };
  // Match the Palace LoadMesh flags: no initial edge generation/refinement; fix orientation.
  auto mesh_a = load(ascii, "ascii"), mesh_b = load(binary, "binary");
  auto &a = *mesh_a;
  auto &b = *mesh_b;
  if (structural_only)
  {
    CheckFullStructure(a, b);
    return;
  }
  REQUIRE(a.Dimension() == 3);
  REQUIRE(a.SpaceDimension() == 3);
  REQUIRE(b.Dimension() == a.Dimension());
  REQUIRE(b.SpaceDimension() == a.SpaceDimension());
  REQUIRE(a.GetNE() > 0);
  REQUIRE(a.GetNBE() > 0);
  REQUIRE(a.GetNV() == b.GetNV());
  REQUIRE(a.GetNE() == b.GetNE());
  REQUIRE(a.GetNBE() == b.GetNBE());
  CHECK(a.CheckElementOrientation(false) == 0);
  CHECK(b.CheckElementOrientation(false) == 0);
  CHECK(a.CheckBdrElementOrientation(false) == 0);
  CHECK(b.CheckBdrElementOrientation(false) == 0);
  for (int v = 0; v < a.GetNV(); v++)
  {
    CHECK(std::memcmp(a.GetVertex(v), b.GetVertex(v), 3 * sizeof(double)) == 0);
  }
  REQUIRE(a.GetNodes());
  REQUIRE(b.GetNodes());
  REQUIRE(a.GetNodes()->Size() == b.GetNodes()->Size());
  REQUIRE(a.GetNodes()->FESpace()->GetMaxElementOrder() == 2);
  REQUIRE(b.GetNodes()->FESpace()->GetMaxElementOrder() == 2);
  CHECK(a.GetNodes()->FESpace()->GetOrdering() == b.GetNodes()->FESpace()->GetOrdering());
  CHECK(std::string(a.GetNodes()->FESpace()->FEColl()->Name()) ==
        b.GetNodes()->FESpace()->FEColl()->Name());
  const bool node_bits_equal = std::memcmp(a.GetNodes()->HostRead(), b.GetNodes()->HostRead(),
                                          a.GetNodes()->Size() * sizeof(double)) == 0;
  REQUIRE(node_bits_equal);
  CheckIntArrays(a.attributes, b.attributes);
  CheckIntArrays(a.bdr_attributes, b.bdr_attributes);
  CheckAttributeNames(a.attribute_sets, b.attribute_sets);
  CheckAttributeNames(a.bdr_attribute_sets, b.bdr_attribute_sets);
  REQUIRE(a.attribute_sets.AttributeSetExists("dielectric"));
  REQUIRE(a.bdr_attribute_sets.AttributeSetExists("port_boundary"));
  CheckElements(a, b, false);
  CheckElements(a, b, true);

  mfem::ND_FECollection fec(2, 3);
  mfem::FiniteElementSpace sa(&a, &fec), sb(&b, &fec);
  REQUIRE(sa.GetVSize() == sb.GetVSize());
  REQUIRE(sa.GetTrueVSize() == sb.GetTrueVSize());
  CHECK(a.GetNEdges() == b.GetNEdges());
  CHECK(a.GetNFaces() == b.GetNFaces());
  for (int e = 0; e < a.GetNE(); e++)
  {
    mfem::Array<int> da, db;
    sa.GetElementDofs(e, da);
    sb.GetElementDofs(e, db);
    CheckIntArrays(da, db);
  }
  mfem::ConstantCoefficient one(1.0);
  double max_operator_rel = 0.0;
  for (bool curl : {false, true})
  {
    auto aa = Assemble(sa, one, curl);
    auto ab = Assemble(sb, one, curl);
    for (unsigned seed : {42u, 314159u, 271828u})
    {
      std::mt19937_64 generator(seed);
      std::uniform_real_distribution<double> random(-1.0, 1.0);
      mfem::Vector x(sa.GetVSize()), ya(x.Size()), yb(x.Size());
      for (int i = 0; i < x.Size(); i++)
      {
        x(i) = random(generator);
      }
      aa->SpMat().Mult(x, ya);
      ab->SpMat().Mult(x, yb);
      const double norm = ya.Norml2();
      REQUIRE(std::isfinite(norm));
      REQUIRE(norm > 0.0);
      yb -= ya;
      const double relative = yb.Norml2() / norm;
      CHECK(relative <= 1e-12);
      max_operator_rel = std::max(max_operator_rel, relative);
      std::fprintf(stderr, "PALACE_IO06_ACTION {\"kind\":\"%s\",\"seed\":%u,\"relative_l2\":%.17g}\n",
                   curl ? "curl" : "mass", seed, relative);
    }
  }

  mfem::GridFunction ga(&sa), gb(&sb);
  for (int i = 0; i < ga.Size(); i++)
  {
    ga(i) = gb(i) = std::sin(0.31 * i);
  }
  double max_field_abs = 0.0;
  for (int e = 0; e < a.GetNE(); e++)
  {
    const auto &rule = mfem::IntRules.Get(a.GetElementBaseGeometry(e), 5);
    for (int q = 0; q < rule.GetNPoints(); q++)
    {
      const auto &ip = rule.IntPoint(q);
      mfem::Vector va, vb, ca, cb;
      ga.GetVectorValue(e, ip, va);
      gb.GetVectorValue(e, ip, vb);
      auto *ta = a.GetElementTransformation(e);
      auto *tb = b.GetElementTransformation(e);
      ta->SetIntPoint(&ip);
      tb->SetIntPoint(&ip);
      ga.GetCurl(*ta, ca);
      gb.GetCurl(*tb, cb);
      for (auto pair : {std::make_pair(&va, &vb), std::make_pair(&ca, &cb)})
      {
        REQUIRE(pair.first->Size() == pair.second->Size());
        *pair.second -= *pair.first;
        const double error = pair.second->Norml2();
        CHECK(error <= 1e-12 * std::max(1.0, pair.first->Norml2()));
        max_field_abs = std::max(max_field_abs, error);
      }
    }
  }
  std::fprintf(stderr,
               "PALACE_IO06_NATIVE {\"vertices\":%d,\"elements\":%d,\"boundary_elements\":%d,"
               "\"coordinate_values\":%d,\"node_bits_equal\":true,\"nd_dofs\":%d,"
               "\"max_operator_relative_l2\":%.17g,\"max_field_absolute_l2\":%.17g}\n",
               a.GetNV(), a.GetNE(), a.GetNBE(), a.GetNodes()->Size(), sa.GetVSize(),
               max_operator_rel, max_field_abs);
}
