// SPDX-License-Identifier: Apache-2.0
// CPU replay of saved single-rank fields using the actual Palace mesh loader.
#include <complex>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <map>
#include <string>
#include <nlohmann/json.hpp>
#include "utils/geodata.hpp"
#include "utils/iodata.hpp"
#include "utils/communication.hpp"

using json = nlohmann::json;
using C = std::complex<double>;
using namespace palace;

mfem::IntegrationRule PositiveRule(int order)
{
  const auto &line = mfem::IntRules.Get(mfem::Geometry::SEGMENT, order+3);
  mfem::IntegrationRule rule(line.GetNPoints()*line.GetNPoints()*line.GetNPoints());
  int n = 0;
  for (int i = 0; i < line.GetNPoints(); ++i)
  for (int j = 0; j < line.GetNPoints(); ++j)
  for (int k = 0; k < line.GetNPoints(); ++k)
  {
    const auto &u = line.IntPoint(i), &v = line.IntPoint(j), &w = line.IntPoint(k);
    auto &ip = rule.IntPoint(n++);
    ip.Set3(u.x, (1-u.x)*v.x, (1-u.x)*(1-v.x)*w.x);
    ip.weight = u.weight*v.weight*w.weight*(1-u.x)*(1-u.x)*(1-v.x);
  }
  double sum = 0.; for (int i=0;i<rule.GetNPoints();++i) sum += rule.IntPoint(i).weight;
  MFEM_VERIFY(std::abs(sum-1./6.) < 1e-14, "Positive Duffy quadrature volume control failed");
  return rule;
}

json Read(const std::string &path)
{
  std::ifstream in(path); json j; in >> j; return j;
}

void Snapshot(const std::string &path, mfem::GridFunction &re, mfem::GridFunction &im)
{
  std::ifstream in(path, std::ios::binary);
  char magic[8]; std::uint64_t n = 0;
  in.read(magic, 8); in.read(reinterpret_cast<char *>(&n), 8);
  MFEM_VERIFY(std::string(magic, 8) == "PALF64V1" && n == re.Size(), "Snapshot DOF/header mismatch");
  in.read(reinterpret_cast<char *>(re.HostWrite()), 8*n);
  in.read(reinterpret_cast<char *>(im.HostWrite()), 8*n);
  MFEM_VERIFY(in.good() && in.peek() == EOF, "Snapshot length mismatch");
}

struct Norm
{
  double ref = 0., cand = 0., err = 0., phase2 = 0., undefined = 0.;
  C correlation = 0.; int points = 0;
  void Add(const mfem::Vector &rr, const mfem::Vector &ri,
           const mfem::Vector &cr, const mfem::Vector &ci, double w)
  {
    double r2 = 0., c2 = 0., d2 = 0.; C dot = 0.;
    for (int k = 0; k < 3; ++k)
    {
      C r(rr[k], ri[k]), c(cr[k], ci[k]);
      r2 += std::norm(r); c2 += std::norm(c); d2 += std::norm(c-r);
      dot += std::conj(r)*c;
    }
    ref += w*r2; cand += w*c2; err += w*d2; correlation += w*dot; ++points;
    // No global or local phase fitting. Near-zero candidate/correlation is undefined.
    if (r2 > 0. && c2 > 0. && std::abs(dot) > 1e-14*std::sqrt(r2*c2))
      phase2 += w*r2*std::pow(std::arg(dot), 2);
    else undefined += w*r2;
  }
  json Result() const
  {
    MFEM_VERIFY(ref > 0. && std::isfinite(ref) && std::isfinite(err), "Empty/invalid ROI norm");
    constexpr double deg = 180./3.14159265358979323846;
    return {{"reference_norm_squared",ref},{"candidate_norm_squared",cand},
            {"relative_complex_L2",std::sqrt(err/ref)},
            {"phase_rms_degrees",deg*std::sqrt(phase2/ref)},
            {"correlation_phase_degrees",deg*std::arg(correlation)},
            {"phase_undefined_reference_fraction",undefined/ref},{"points",points}};
  }
};

int main(int argc, char **argv)
{
  Mpi::Init(argc, argv); mfem::Device device("cpu");
  MFEM_VERIFY(argc == 2 && Mpi::Size(MPI_COMM_WORLD) == 1, "One rank and case.json required");
  auto job = Read(argv[1]); std::string reference = job["reference"], candidate = job["candidate"];
  auto config = Read(reference+"/config.json");
  config["Model"]["Mesh"] = reference+"/"+config["Model"]["Mesh"].get<std::string>();
  IoData io(config, false);
  MFEM_VERIFY(io.model.refinement.uniform_ref_levels == 0 && io.model.refinement.max_it == 0,
              "Replay currently requires frozen unrefined single-rank mesh");
  auto serial = mesh::Load(io, MPI_COMM_WORLD);
  std::cout << "ROI_PHASE serial_mesh_loaded" << std::endl;
  if (!(io.model.Lc > 0.)) io.model.Lc = mesh::ComputeReferenceLength(serial, MPI_COMM_WORLD);
  io.NondimensionalizeInputs(serial);
  std::vector<std::unique_ptr<mfem::ParMesh>> meshes;
  meshes.push_back(mesh::Partition(io, std::move(serial), MPI_COMM_WORLD));
  mesh::RefineMesh(io, meshes);
  auto &mesh = *meshes.back();
  mfem::ND_FECollection nd(io.solver.order, 3, mfem::BasisType::GaussLobatto, mfem::BasisType::GaussLegendre);
  mfem::RT_FECollection rt(io.solver.order-1, 3, mfem::BasisType::GaussLobatto, mfem::BasisType::GaussLegendre);
  mfem::ParFiniteElementSpace es(&mesh, &nd), bs(&mesh, &rt);
  std::cout << "ROI_PHASE spaces_created E=" << es.GetVSize() << " B=" << bs.GetVSize() << std::endl;
  json result = {{"device","cpu"},{"elements",mesh.GetNE()},
                 {"E_dofs",es.GetVSize()},{"B_dofs",bs.GetVSize()},
                 {"entries",json::array()},{"mesh_loader","actual linked Palace Load/Partition/RefineMesh"}};
  const bool tiny = job["mode"] == "coax";
  auto pairs = job.value("pairs", json::array({{{"reference",reference},{"candidate",candidate},{"frequency_ghz",0.}}}));
  for (const auto &pair : pairs)
  {
  reference = pair["reference"]; candidate = pair["candidate"];
  for (int port = 1; port <= 2; ++port)
  for (const std::string field : {"E", "B"})
  {
    const auto part = job.value("part", std::string("all"));
    if (part != "all" && part != std::to_string(port)+field) continue;
    auto *space = field == "E" ? &es : &bs;
    mfem::GridFunction rr(space), ri(space), cr(space), ci(space);
    const auto file = "/fields/s"+std::to_string(port)+"-f0-"+field+".bin";
    Snapshot(reference+file, rr, ri); Snapshot(candidate+file, cr, ci);
    std::cout << "ROI_PHASE snapshots_loaded port=" << port << " field=" << field << std::endl;
    for (int order : {4,6})
    {
      auto rule = PositiveRule(order);
      // All cells are the same-order tetrahedron: reference basis values are
      // invariant across cells. Cache those; apply only the physical Piola map.
      std::vector<mfem::DenseMatrix> reference_shape(rule.GetNPoints());
      for (int p=0;p<rule.GetNPoints();++p)
      {
        reference_shape[p].SetSize(space->GetFE(0)->GetDof(),3);
        space->GetFE(0)->CalcVShape(rule.IntPoint(p), reference_shape[p]);
      }
      std::map<std::string,Norm> norms;
      for (int el = 0; el < mesh.GetNE(); ++el)
      {
        const int attr = mesh.GetAttribute(el);
        if (!tiny && attr != 2 && attr != 3) continue;
        auto &tr = *mesh.GetElementTransformation(el);
        MFEM_VERIFY(mesh.GetElementBaseGeometry(el) == mfem::Geometry::TETRAHEDRON,
                    "This replay supports tetrahedra only");
        mfem::Vector r(3), i(3), c(3), d(3), xyz(3);
        // Extract and orient coefficients once per cell, not four times per point.
        // Same signed-DOF/InvTransformPrimal convention as MFEM GridFunction.
        mfem::Array<int> dofs;
        auto *transform = space->GetElementVDofs(el, dofs);
        mfem::Vector lr(dofs.Size()), li(dofs.Size()), lc(dofs.Size()), ld(dofs.Size());
        rr.GetSubVector(dofs,lr); ri.GetSubVector(dofs,li);
        cr.GetSubVector(dofs,lc); ci.GetSubVector(dofs,ld);
        if (transform)
        {
          transform->InvTransformPrimal(lr); transform->InvTransformPrimal(li);
          transform->InvTransformPrimal(lc); transform->InvTransformPrimal(ld);
        }
        mfem::DenseMatrix shape(dofs.Size(),3);
        for (int p = 0; p < rule.GetNPoints(); ++p)
        {
          const auto &ip = rule.IntPoint(p); tr.SetIntPoint(&ip);
          tr.Transform(ip, xyz); xyz *= io.units.GetMeshLengthRelativeScale();
          if (field == "E") mfem::Mult(reference_shape[p],tr.InverseJacobian(),shape);
          else
          {
            mfem::MultABt(reference_shape[p],tr.Jacobian(),shape);
            shape *= 1./tr.Weight();
          }
          shape.MultTranspose(lr,r); shape.MultTranspose(li,i);
          shape.MultTranspose(lc,c); shape.MultTranspose(ld,d);
          const double w = ip.weight*tr.Weight();
          MFEM_VERIFY(w > 0., "Positive physical quadrature required");
          if (tiny) norms["coax"].Add(r,i,c,d,w);
          else if (attr == 3) norms["feed-PTFE"].Add(r,i,c,d,w);
          else
          {
            norms["PCB"].Add(r,i,c,d,w);
            // Four fixed PCB sectors outside the central feed (radius >=6 mm).
            // Includes dielectric beside slots; does not assert pointwise slot-tip accuracy.
            if (xyz[0]*xyz[0]+xyz[1]*xyz[1] >= 36.)
              norms[std::string("slot-sector-")+(xyz[0]>=0?"P":"N")+(xyz[1]>=0?"P":"N")].Add(r,i,c,d,w);
          }
        }
      }
      for (auto &[name,norm] : norms)
      {
        auto row = norm.Result(); row["roi"] = name; row["port"] = port;
        row["field"] = field; row["quadrature"] = order;
        row["frequency_ghz"] = pair["frequency_ghz"];
        result["entries"].push_back(row);
      }
      std::cout << "ROI_PHASE quadrature_finished port=" << port << " field=" << field << " level=" << order << std::endl;
      // Preserve progress; incomplete chunks are never accepted as full coverage.
      std::ofstream(job["output"].get<std::string>()) << result.dump(2) << '\n';
    }
  }
  }
  std::ofstream(job["output"].get<std::string>()) << result.dump(2) << '\n';
}
