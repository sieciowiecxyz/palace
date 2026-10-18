// Small independent bridge to installed MFEM, not a Palace solver change.
#include <mfem.hpp>

extern "C" const char *mfem_bridge_version() { return mfem::GetVersionStr(); }
extern "C" const char *mfem_bridge_git() { return mfem::GetGitStr(); }

extern "C" int mfem_nd1_reference(int count, const double *points,
                                  double *values, double *curls)
{
  if (count <= 0 || !points || !values || !curls) { return 1; }
  mfem::ND_TetrahedronElement fe(1);
  if (fe.GetDof() != 6) { return 2; }
  mfem::DenseMatrix v(6, 3), c(6, 3);
  for (int p = 0; p < count; p++)
  {
    mfem::IntegrationPoint ip;
    ip.Set3(points[3*p], points[3*p+1], points[3*p+2]);
    fe.CalcVShape(ip, v);
    fe.CalcCurlShape(ip, c);
    for (int i = 0; i < 6; i++)
    {
      for (int j = 0; j < 3; j++)
      {
        values[18*p+3*i+j] = v(i,j);
        curls[18*p+3*i+j] = c(i,j);
      }
    }
  }
  return 0;
}

extern "C" int mfem_nd1_elements(int count, const double *vertices,
                                 double *mass, double *curl)
{
  if (count <= 0 || !vertices || !mass || !curl) { return 1; }
  mfem::ND_TetrahedronElement fe(1);
  mfem::VectorFEMassIntegrator mass_integrator;
  mfem::CurlCurlIntegrator curl_integrator;
  mfem::DenseMatrix m(6), k(6), point_matrix(3,4);
  mfem::IsoparametricTransformation transformation;
  transformation.SetIdentityTransformation(mfem::Geometry::TETRAHEDRON);
  for (int e = 0; e < count; e++)
  {
    for (int i = 0; i < 4; i++)
    {
      for (int j = 0; j < 3; j++) { point_matrix(j,i) = vertices[12*e+3*i+j]; }
    }
    transformation.SetPointMat(point_matrix);
    mass_integrator.AssembleElementMatrix(fe, transformation, m);
    curl_integrator.AssembleElementMatrix(fe, transformation, k);
    for (int i = 0; i < 6; i++)
    {
      for (int j = 0; j < 6; j++)
      {
        mass[36*e+6*i+j] = m(i,j);
        curl[36*e+6*i+j] = k(i,j);
      }
    }
  }
  return 0;
}
