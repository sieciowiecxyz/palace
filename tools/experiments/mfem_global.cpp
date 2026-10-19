// Isolated serial MFEM ND1/ND2 validation bridge. No Palace defaults change.
#include <mfem.hpp>
#include <algorithm>
#include <cmath>
#include <memory>

namespace
{
struct GlobalND
{
  std::unique_ptr<mfem::Mesh> mesh;
  std::unique_ptr<mfem::ND_FECollection> collection;
  std::unique_ptr<mfem::FiniteElementSpace> space;
  std::unique_ptr<mfem::BilinearForm> mass, curl;
  mfem::Array<int> boundary;
  int nonidentity = 0;
};
}

extern "C" void *mfem_global_create(int nv, const double *vertices, int nt,
                                     const int *tetrahedra, int nb,
                                     const int *faces, int order)
{
  if (nv < 4 || nt < 1 || nb < 4 || !vertices || !tetrahedra || !faces ||
      (order != 1 && order != 2)) { return nullptr; }
  auto result = std::make_unique<GlobalND>();
  result->mesh = std::make_unique<mfem::Mesh>(3, nv, nt, nb, 3);
  for (int i = 0; i < nv; i++) { result->mesh->AddVertex(vertices + 3*i); }
  for (int i = 0; i < nt; i++) { result->mesh->AddTet(tetrahedra + 4*i, 1); }
  for (int i = 0; i < nb; i++) { result->mesh->AddBdrTriangle(faces + 3*i, 1); }
  result->mesh->FinalizeTetMesh(1, 0, false);
  result->collection = std::make_unique<mfem::ND_FECollection>(order, 3);
  result->space = std::make_unique<mfem::FiniteElementSpace>(result->mesh.get(),
                                                           result->collection.get());
  result->mass = std::make_unique<mfem::BilinearForm>(result->space.get());
  result->mass->AddDomainIntegrator(new mfem::VectorFEMassIntegrator());
  result->mass->Assemble();
  result->mass->Finalize();
  result->curl = std::make_unique<mfem::BilinearForm>(result->space.get());
  result->curl->AddDomainIntegrator(new mfem::CurlCurlIntegrator());
  result->curl->Assemble();
  result->curl->Finalize();
  mfem::Array<int> attributes(result->mesh->bdr_attributes.Max());
  attributes = 1;
  result->space->GetEssentialTrueDofs(attributes, result->boundary);
  for (int i = 0; i < nt; i++)
  {
    mfem::Array<int> dofs;
    mfem::DofTransformation transformation;
    result->space->GetElementDofs(i, dofs, transformation);
    // IsIdentity() only describes the transformation class, not this cell's
    // face orientations. Count an actual change of the local coordinate basis.
    bool changed = false;
    if (!transformation.IsIdentity())
    {
      for (int j = 0; j < dofs.Size(); j++)
      {
        mfem::Vector unit(dofs.Size());
        unit = 0.;
        unit[j] = 1.;
        transformation.InvTransformPrimal(unit);
        for (int k = 0; k < unit.Size(); k++)
        { changed = changed || std::abs(unit[k] - (j == k ? 1. : 0.)) > 1e-14; }
      }
    }
    result->nonidentity += changed;
  }
  return result.release();
}

extern "C" void mfem_global_destroy(void *handle)
{ delete static_cast<GlobalND *>(handle); }

extern "C" int mfem_global_info(void *handle, int *info)
{
  if (!handle || !info) { return 1; }
  auto &g = *static_cast<GlobalND *>(handle);
  info[0] = g.space->GetNDofs();
  info[1] = g.space->GetFE(0)->GetDof();
  info[2] = g.mass->SpMat().NumNonZeroElems();
  info[3] = g.curl->SpMat().NumNonZeroElems();
  info[4] = g.boundary.Size();
  info[5] = g.nonidentity;
  return 0;
}

extern "C" int mfem_global_matrix(void *handle, int which, int *rows,
                                     int *columns, double *values)
{
  if (!handle || !rows || !columns || !values || (which != 0 && which != 1)) { return 1; }
  auto &g = *static_cast<GlobalND *>(handle);
  const auto &a = which == 0 ? g.mass->SpMat() : g.curl->SpMat();
  std::copy(a.GetI(), a.GetI() + a.Height() + 1, rows);
  std::copy(a.GetJ(), a.GetJ() + a.NumNonZeroElems(), columns);
  std::copy(a.GetData(), a.GetData() + a.NumNonZeroElems(), values);
  return 0;
}

extern "C" int mfem_global_boundary(void *handle, int *dofs)
{
  if (!handle || !dofs) { return 1; }
  auto &g = *static_cast<GlobalND *>(handle);
  std::copy(g.boundary.GetData(), g.boundary.GetData() + g.boundary.Size(), dofs);
  return 0;
}

extern "C" int mfem_global_basis(void *handle, int cell, int count,
                                    const double *points, int *indices,
                                    double *values, double *curls)
{
  if (!handle || !points || !indices || !values || !curls || count < 1) { return 1; }
  auto &g = *static_cast<GlobalND *>(handle);
  if (cell < 0 || cell >= g.mesh->GetNE()) { return 2; }
  const auto *fe = g.space->GetFE(cell);
  const int nd = fe->GetDof();
  mfem::Array<int> dofs;
  mfem::DofTransformation transformation;
  g.space->GetElementDofs(cell, dofs, transformation);
  mfem::DenseMatrix local_to_global(nd);
  for (int i = 0; i < nd; i++)
  {
    indices[i] = dofs[i] >= 0 ? dofs[i] : -1-dofs[i];
    mfem::Vector unit(nd);
    unit = 0.;
    unit[i] = dofs[i] >= 0 ? 1. : -1.;
    if (!transformation.IsIdentity()) { transformation.InvTransformPrimal(unit); }
    for (int j = 0; j < nd; j++) { local_to_global(j,i) = unit[j]; }
  }
  auto *tr = g.mesh->GetElementTransformation(cell);
  mfem::DenseMatrix v(nd,3), c(nd,3);
  for (int p = 0; p < count; p++)
  {
    mfem::IntegrationPoint ip;
    ip.Set3(points[3*p], points[3*p+1], points[3*p+2]);
    tr->SetIntPoint(&ip);
    fe->CalcVShape(*tr,v);
    fe->CalcPhysCurlShape(*tr,c);
    for (int i = 0; i < nd; i++)
    {
      for (int d = 0; d < 3; d++)
      {
        double value = 0., curl = 0.;
        for (int j = 0; j < nd; j++)
        {
          value += local_to_global(j,i)*v(j,d);
          curl += local_to_global(j,i)*c(j,d);
        }
        values[(p*nd+i)*3+d] = value;
        curls[(p*nd+i)*3+d] = curl;
      }
    }
  }
  return 0;
}

extern "C" int mfem_global_project(void *handle, int kind, int imaginary,
                                      double k, double *coefficients)
{
  if (!handle || !coefficients || kind < 0 || kind > 3 ||
      (imaginary != 0 && imaginary != 1) || !std::isfinite(k)) { return 1; }
  auto &g = *static_cast<GlobalND *>(handle);
  mfem::VectorFunctionCoefficient field(3, [=](const mfem::Vector &x, mfem::Vector &v)
  {
    v = 0.;
    if (kind == 0 && !imaginary) { v[0] = 1.; }
    else if (kind == 1 && !imaginary) { v[0] = x[2]; v[1] = x[0]; v[2] = x[1]; }
    else if (kind >= 2) { v[kind == 2 ? 0 : 1] = imaginary ? std::sin(k*x[2]) : std::cos(k*x[2]); }
  });
  mfem::GridFunction projected(g.space.get());
  projected.ProjectCoefficient(field);
  std::copy(projected.GetData(), projected.GetData() + projected.Size(), coefficients);
  return 0;
}

extern "C" int mfem_global_evaluate(void *handle, int cell, int count,
                                       const double *points, const double *coefficients,
                                       double *values, double *curls)
{
  if (!handle || !points || !coefficients || !values || !curls || count < 1) { return 1; }
  auto &g = *static_cast<GlobalND *>(handle);
  if (cell < 0 || cell >= g.mesh->GetNE()) { return 2; }
  mfem::GridFunction field(g.space.get());
  std::copy(coefficients, coefficients + field.Size(), field.GetData());
  auto *tr = g.mesh->GetElementTransformation(cell);
  mfem::Vector v(3), c(3);
  for (int p = 0; p < count; p++)
  {
    mfem::IntegrationPoint ip;
    ip.Set3(points[3*p], points[3*p+1], points[3*p+2]);
    tr->SetIntPoint(&ip);
    field.GetVectorValue(cell,ip,v);
    field.GetCurl(*tr,c);
    for (int d = 0; d < 3; d++) { values[3*p+d] = v[d]; curls[3*p+d] = c[d]; }
  }
  return 0;
}
