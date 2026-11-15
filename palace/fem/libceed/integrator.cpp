// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include "integrator.hpp"
#include "restriction.hpp"
#include "utils/stageprofile.hpp"
#include <algorithm>
#include <cstdlib>
#include <cstring>

#include <string>
#include <ceed/backend.h>
#include <mfem.hpp>
#include "utils/diagnostic.hpp"

PalacePragmaDiagnosticPush
PalacePragmaDiagnosticDisableUnused

#include "fem/qfunctions/coeff/coeff_qf.h"
#include "fem/qfunctions/apply_qf.h"
#include "fem/qfunctions/geom_qf.h"

PalacePragmaDiagnosticPop

namespace palace::ceed
{

namespace
{

// Only the 3D H(curl) mass build/apply paths have this single 3x3 context.
// Other QFunction layouts retain their original path. No numerical threshold is used.
std::vector<CeedInt> NonzeroMassElements(const CeedQFunctionInfo &info, const void *ctx,
                                       std::size_t ctx_size, Ceed ceed,
                                       CeedVector geom_data,
                                       CeedElemRestriction geom_restr)
{
  const char *enabled = std::getenv("PALACE_EXACT_ZERO_SUBSET");
  const bool mass_only =
      info.apply_qf_path.find("33/hcurl_build_33_qf.h:") != std::string::npos ||
      info.apply_qf_path.find("33/hcurl_33_qf.h:") != std::string::npos;
  if ((enabled && std::strcmp(enabled, "0") == 0) || !mass_only)
  {
    return {};
  }
  StageProfile profile("operators.exact_zero_subset");
  if (!ctx || ctx_size < 2 * sizeof(CeedIntScalar))
  {
    return {};
  }
  const auto *coeff = static_cast<const CeedIntScalar *>(ctx);
  const CeedInt na = coeff[0].first;
  const auto count = ctx_size / sizeof(CeedIntScalar);
  if (na <= 0 || static_cast<std::size_t>(na) + 2 > count)
  {
    return {};
  }
  const CeedInt nm = coeff[1 + na].first;
  if (nm <= 0 || static_cast<std::size_t>(na) + 2 + 9 * static_cast<std::size_t>(nm) != count)
  {
    return {};
  }
  std::vector<bool> zero(na);
  bool has_zero = false;
  for (CeedInt a = 0; a < na; a++)
  {
    const CeedInt mat = coeff[1 + a].first;
    if (mat < 0 || mat >= nm)
    {
      return {};
    }
    zero[a] = true;
    for (CeedInt j = 0; j < 9; j++)
    {
      // NaN and every nonzero (including subnormal values) must remain active.
      zero[a] = zero[a] && (coeff[2 + na + 9 * mat + j].second == 0.0);
    }
    has_zero = has_zero || zero[a];
  }
  if (!has_zero)
  {
    return {};
  }
  CeedRestrictionType type;
  CeedInt ne, nc, block, strides[3];
  PalaceCeedCall(ceed, CeedElemRestrictionGetType(geom_restr, &type));
  PalaceCeedCall(ceed, CeedElemRestrictionGetBlockSize(geom_restr, &block));
  PalaceCeedCall(ceed, CeedElemRestrictionGetNumElements(geom_restr, &ne));
  PalaceCeedCall(ceed, CeedElemRestrictionGetNumComponents(geom_restr, &nc));
  if (type != CEED_RESTRICTION_STRIDED || block != 1 || nc != 11)
  {
    return {};
  }
  PalaceCeedCall(ceed, CeedElemRestrictionGetLLayout(geom_restr, strides));
  const CeedScalar *geometry;
  PalaceCeedCall(ceed, CeedVectorGetArrayRead(geom_data, CEED_MEM_HOST, &geometry));
  std::vector<CeedInt> elements;
  for (CeedInt e = 0; e < ne; e++)
  {
    // Mesh attributes are constant on each element, stored in geometry component zero.
    const auto attr_value = geometry[static_cast<CeedSize>(e) * strides[2]];
    MFEM_VERIFY(attr_value >= 1 && attr_value <= na, "Invalid geometry attribute!");
    const CeedInt attr = static_cast<CeedInt>(attr_value);
    MFEM_VERIFY(attr_value == attr, "Nonintegral geometry attribute!");
    if (!zero[attr - 1])
    {
      elements.push_back(e);
    }
  }
  PalaceCeedCall(ceed, CeedVectorRestoreArrayRead(geom_data, &geometry));
  const char *trace = std::getenv("PALACE_STAGE_TRACE");
  if (trace && std::strcmp(trace, "1") == 0)
  {
    std::fprintf(stderr, "PALACE_EXACT_ZERO_SUBSET elements=%d active=%zu\n", ne,
                 elements.size());
  }
  // Empty/all-active cases retain the original operator; no empty-composite changes.
  if (elements.empty() || elements.size() == static_cast<std::size_t>(ne))
  {
    return {};
  }
  return elements;
}

void AddQFunctionActiveInputs(unsigned int ops, Ceed ceed, CeedBasis basis,
                              CeedQFunction qf, std::string name = "u")
{
  // Add inputs or outputs with evaluation modes for the active vector of a QFunction.
  CeedInt num_comp;
  PalaceCeedCall(ceed, CeedBasisGetNumComponents(basis, &num_comp));
  if (ops & EvalMode::None)
  {
    PalaceCeedCall(ceed, CeedQFunctionAddInput(qf, name.c_str(), num_comp, CEED_EVAL_NONE));
  }
  if (ops & EvalMode::Interp)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_INTERP, &q_comp));
    PalaceCeedCall(
        ceed, CeedQFunctionAddInput(qf, name.c_str(), num_comp * q_comp, CEED_EVAL_INTERP));
  }
  if (ops & EvalMode::Grad)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_GRAD, &q_comp));
    PalaceCeedCall(ceed, CeedQFunctionAddInput(qf, (std::string("grad_") + name).c_str(),
                                               num_comp * q_comp, CEED_EVAL_GRAD));
  }
  if (ops & EvalMode::Div)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_DIV, &q_comp));
    PalaceCeedCall(ceed, CeedQFunctionAddInput(qf, (std::string("div_") + name).c_str(),
                                               num_comp * q_comp, CEED_EVAL_DIV));
  }
  if (ops & EvalMode::Curl)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_CURL, &q_comp));
    PalaceCeedCall(ceed, CeedQFunctionAddInput(qf, (std::string("curl_") + name).c_str(),
                                               num_comp * q_comp, CEED_EVAL_CURL));
  }
}

void AddQFunctionActiveOutputs(unsigned int ops, Ceed ceed, CeedBasis basis,
                               CeedQFunction qf, std::string name = "v")
{
  // Add inputs or outputs with evaluation modes for the active vector of a QFunction.
  CeedInt num_comp;
  PalaceCeedCall(ceed, CeedBasisGetNumComponents(basis, &num_comp));
  if (ops & EvalMode::None)
  {
    PalaceCeedCall(ceed,
                   CeedQFunctionAddOutput(qf, name.c_str(), num_comp, CEED_EVAL_NONE));
  }
  if (ops & EvalMode::Interp)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_INTERP, &q_comp));
    PalaceCeedCall(ceed, CeedQFunctionAddOutput(qf, name.c_str(), num_comp * q_comp,
                                                CEED_EVAL_INTERP));
  }
  if (ops & EvalMode::Grad)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_GRAD, &q_comp));
    PalaceCeedCall(ceed, CeedQFunctionAddOutput(qf, (std::string("grad_") + name).c_str(),
                                                num_comp * q_comp, CEED_EVAL_GRAD));
  }
  if (ops & EvalMode::Div)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_DIV, &q_comp));
    PalaceCeedCall(ceed, CeedQFunctionAddOutput(qf, (std::string("div_") + name).c_str(),
                                                num_comp * q_comp, CEED_EVAL_DIV));
  }
  if (ops & EvalMode::Curl)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_CURL, &q_comp));
    PalaceCeedCall(ceed, CeedQFunctionAddOutput(qf, (std::string("curl_") + name).c_str(),
                                                num_comp * q_comp, CEED_EVAL_CURL));
  }
}

void AddOperatorActiveFields(unsigned int ops, Ceed ceed, CeedElemRestriction restr,
                             CeedBasis basis, CeedOperator op, const std::string &name,
                             CeedVector v)
{
  // Set active input or output vector fields of an operator.
  if (ops & EvalMode::None)
  {
    PalaceCeedCall(ceed, CeedOperatorSetField(op, name.c_str(), restr, CEED_BASIS_NONE, v));
  }
  if (ops & EvalMode::Interp)
  {
    PalaceCeedCall(ceed, CeedOperatorSetField(op, name.c_str(), restr, basis, v));
  }
  if (ops & EvalMode::Grad)
  {
    PalaceCeedCall(ceed, CeedOperatorSetField(op, (std::string("grad_") + name).c_str(),
                                              restr, basis, v));
  }
  if (ops & EvalMode::Div)
  {
    PalaceCeedCall(ceed, CeedOperatorSetField(op, (std::string("div_") + name).c_str(),
                                              restr, basis, v));
  }
  if (ops & EvalMode::Curl)
  {
    PalaceCeedCall(ceed, CeedOperatorSetField(op, (std::string("curl_") + name).c_str(),
                                              restr, basis, v));
  }
}

void AddOperatorActiveInputFields(unsigned int ops, Ceed ceed, CeedElemRestriction restr,
                                  CeedBasis basis, CeedOperator op, std::string name = "u",
                                  CeedVector v = CEED_VECTOR_ACTIVE)
{
  AddOperatorActiveFields(ops, ceed, restr, basis, op, name, v);
}

void AddOperatorActiveOutputFields(unsigned int ops, Ceed ceed, CeedElemRestriction restr,
                                   CeedBasis basis, CeedOperator op, std::string name = "v",
                                   CeedVector v = CEED_VECTOR_ACTIVE)
{
  AddOperatorActiveFields(ops, ceed, restr, basis, op, name, v);
}

std::vector<CeedInt> QuadratureDataSetup(unsigned int ops, Ceed ceed,
                                         CeedElemRestriction restr, CeedBasis basis,
                                         CeedVector *q_data,
                                         CeedElemRestriction *q_data_restr)
{
  // Operator application at each quadrature point should be square, so just use the inputs
  // and ignore the outputs.
  CeedInt num_comp;
  PalaceCeedCall(ceed, CeedBasisGetNumComponents(basis, &num_comp));

  std::vector<CeedInt> active_input_sizes;
  if (ops & EvalMode::None)
  {
    active_input_sizes.push_back(num_comp);
  }
  if (ops & EvalMode::Interp)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_INTERP, &q_comp));
    active_input_sizes.push_back(num_comp * q_comp);
  }
  if (ops & EvalMode::Grad)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_GRAD, &q_comp));
    active_input_sizes.push_back(num_comp * q_comp);
  }
  if (ops & EvalMode::Div)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_DIV, &q_comp));
    active_input_sizes.push_back(num_comp * q_comp);
  }
  if (ops & EvalMode::Curl)
  {
    CeedInt q_comp;
    PalaceCeedCall(ceed,
                   CeedBasisGetNumQuadratureComponents(basis, CEED_EVAL_CURL, &q_comp));
    active_input_sizes.push_back(num_comp * q_comp);
  }

  CeedInt num_elem, num_qpts, q_data_size = 0;
  PalaceCeedCall(ceed, CeedElemRestrictionGetNumElements(restr, &num_elem));
  PalaceCeedCall(ceed, CeedBasisGetNumQuadraturePoints(basis, &num_qpts));
  for (auto size : active_input_sizes)
  {
    q_data_size += size * size;
  }

  PalaceCeedCall(
      ceed, CeedVectorCreate(ceed, (CeedSize)num_elem * num_qpts * q_data_size, q_data));
  PalaceCeedCall(
      ceed, CeedElemRestrictionCreateStrided(ceed, num_elem, num_qpts, q_data_size,
                                             (CeedSize)num_elem * num_qpts * q_data_size,
                                             CEED_STRIDES_BACKEND, q_data_restr));

  return active_input_sizes;
}

void QuadratureDataAssembly(const std::vector<CeedInt> &qf_active_sizes,
                            const CeedQFunctionInfo &info, Ceed ceed,
                            CeedElemRestriction trial_restr, CeedElemRestriction test_restr,
                            CeedBasis trial_basis, CeedBasis test_basis, CeedVector q_data,
                            CeedElemRestriction q_data_restr, CeedOperator *op)
{
  // Assemble the quadrature data, destroy the operator, and create a new one for the
  // actual operator application.
  PalaceCeedCall(ceed,
                 CeedOperatorApply(*op, CEED_VECTOR_NONE, q_data, CEED_REQUEST_IMMEDIATE));
  PalaceCeedCall(ceed, CeedOperatorDestroy(op));

  MFEM_VERIFY(!qf_active_sizes.empty() && qf_active_sizes.size() <= 2,
              "Invalid number of active QFunction input/output fields ("
                  << qf_active_sizes.size() << ")!");
  CeedQFunction apply_qf;
  CeedInt qf_size_1 = qf_active_sizes[0],
          qf_size_2 = (qf_active_sizes.size() > 1) ? qf_active_sizes[1] : 0;
  switch (10 * qf_size_1 + qf_size_2)
  {
    case 1:
    case 10:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_apply_1,
                               PalaceQFunctionRelativePath(f_apply_1_loc), &apply_qf));
      break;
    case 2:
    case 20:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_apply_2,
                               PalaceQFunctionRelativePath(f_apply_2_loc), &apply_qf));
      break;
    case 3:
    case 30:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_apply_3,
                               PalaceQFunctionRelativePath(f_apply_3_loc), &apply_qf));
      break;
    case 22:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_apply_22,
                               PalaceQFunctionRelativePath(f_apply_22_loc), &apply_qf));
      break;
    case 33:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_apply_33,
                               PalaceQFunctionRelativePath(f_apply_33_loc), &apply_qf));
      break;
    case 12:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_apply_12,
                               PalaceQFunctionRelativePath(f_apply_12_loc), &apply_qf));
      break;
    case 13:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_apply_13,
                               PalaceQFunctionRelativePath(f_apply_13_loc), &apply_qf));
      break;
    case 21:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_apply_21,
                               PalaceQFunctionRelativePath(f_apply_21_loc), &apply_qf));
      break;
    case 31:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_apply_31,
                               PalaceQFunctionRelativePath(f_apply_31_loc), &apply_qf));
      break;
    default:
      MFEM_ABORT("Invalid number of QFunction input/output components ("
                 << qf_size_1 << ", " << qf_size_2 << ")!");
      apply_qf = nullptr;  // Silence compiler warning
  }

  // Inputs/outputs.
  {
    CeedInt q_data_size;
    PalaceCeedCall(ceed, CeedElemRestrictionGetNumComponents(q_data_restr, &q_data_size));
    PalaceCeedCall(ceed,
                   CeedQFunctionAddInput(apply_qf, "q_data", q_data_size, CEED_EVAL_NONE));
  }
  AddQFunctionActiveInputs(info.trial_ops, ceed, trial_basis, apply_qf);
  AddQFunctionActiveOutputs(info.test_ops, ceed, test_basis, apply_qf);

  // Create the actual operator.
  PalaceCeedCall(ceed, CeedOperatorCreate(ceed, apply_qf, nullptr, nullptr, op));
  PalaceCeedCall(ceed, CeedQFunctionDestroy(&apply_qf));

  PalaceCeedCall(
      ceed, CeedOperatorSetField(*op, "q_data", q_data_restr, CEED_BASIS_NONE, q_data));
  AddOperatorActiveInputFields(info.trial_ops, ceed, trial_restr, trial_basis, *op);
  AddOperatorActiveOutputFields(info.test_ops, ceed, test_restr, test_basis, *op);

  PalaceCeedCall(ceed, CeedOperatorCheckReady(*op));
}

}  // namespace

int CeedGeometryDataGetSpaceDimension(CeedElemRestriction geom_data_restr, CeedInt dim,
                                      CeedInt *space_dim)
{
  if (space_dim)
  {
    Ceed ceed;
    CeedInt geom_data_size;
    PalaceCeedCallBackend(CeedElemRestrictionGetCeed(geom_data_restr, &ceed));
    PalaceCeedCall(ceed,
                   CeedElemRestrictionGetNumComponents(geom_data_restr, &geom_data_size));
    *space_dim = (geom_data_size - 2) / dim;
    MFEM_ASSERT(2 + (*space_dim) * dim == geom_data_size,
                "Invalid size for geometry quadrature data!");
  }
  return CEED_ERROR_SUCCESS;
}

void AssembleCeedGeometryData(Ceed ceed, CeedElemRestriction mesh_restr,
                              CeedBasis mesh_basis, CeedVector mesh_nodes,
                              CeedElemRestriction attr_restr, CeedBasis attr_basis,
                              CeedVector elem_attr, CeedVector geom_data,
                              CeedElemRestriction geom_data_restr)
{
  CeedInt dim, space_dim, num_qpts;
  PalaceCeedCall(ceed, CeedBasisGetDimension(mesh_basis, &dim));
  PalaceCeedCall(ceed, CeedBasisGetNumComponents(mesh_basis, &space_dim));
  PalaceCeedCall(ceed, CeedBasisGetNumQuadraturePoints(mesh_basis, &num_qpts));

  // Create the QFunction that computes the quadrature data.
  CeedQFunction build_qf;
  switch (10 * space_dim + dim)
  {
    case 22:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_build_geom_factor_22,
                               PalaceQFunctionRelativePath(f_build_geom_factor_22_loc),
                               &build_qf));
      break;
    case 33:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_build_geom_factor_33,
                               PalaceQFunctionRelativePath(f_build_geom_factor_33_loc),
                               &build_qf));
      break;
    case 21:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_build_geom_factor_21,
                               PalaceQFunctionRelativePath(f_build_geom_factor_21_loc),
                               &build_qf));
      break;
    case 31:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_build_geom_factor_31,
                               PalaceQFunctionRelativePath(f_build_geom_factor_31_loc),
                               &build_qf));
      break;
    case 32:
      PalaceCeedCall(ceed, CeedQFunctionCreateInterior(
                               ceed, 1, f_build_geom_factor_32,
                               PalaceQFunctionRelativePath(f_build_geom_factor_32_loc),
                               &build_qf));
      break;
    default:
      MFEM_ABORT("Invalid value of (dim, space_dim) = ("
                 << dim << ", " << space_dim << ") for geometry factor quadrature data!");
      build_qf = nullptr;  // Silence compiler warning
  }

  // Inputs/outputs.
  PalaceCeedCall(ceed, CeedQFunctionAddInput(build_qf, "attr", 1, CEED_EVAL_INTERP));
  PalaceCeedCall(ceed, CeedQFunctionAddInput(build_qf, "q_w", 1, CEED_EVAL_WEIGHT));
  PalaceCeedCall(
      ceed, CeedQFunctionAddInput(build_qf, "grad_x", space_dim * dim, CEED_EVAL_GRAD));
  {
    CeedInt geom_data_size;
    PalaceCeedCall(ceed,
                   CeedElemRestrictionGetNumComponents(geom_data_restr, &geom_data_size));
    MFEM_VERIFY(geom_data_size == 2 + space_dim * dim,
                "Insufficient storage for geometry quadrature data!");
    PalaceCeedCall(ceed, CeedQFunctionAddOutput(build_qf, "geom_data", geom_data_size,
                                                CEED_EVAL_NONE));
  }

  // Create the operator that builds the quadrature data.
  CeedOperator build_op;
  PalaceCeedCall(ceed, CeedOperatorCreate(ceed, build_qf, nullptr, nullptr, &build_op));
  PalaceCeedCall(ceed, CeedQFunctionDestroy(&build_qf));

  PalaceCeedCall(ceed,
                 CeedOperatorSetField(build_op, "attr", attr_restr, attr_basis, elem_attr));
  PalaceCeedCall(ceed, CeedOperatorSetField(build_op, "q_w", CEED_ELEMRESTRICTION_NONE,
                                            mesh_basis, CEED_VECTOR_NONE));
  PalaceCeedCall(ceed, CeedOperatorSetField(build_op, "grad_x", mesh_restr, mesh_basis,
                                            CEED_VECTOR_ACTIVE));
  PalaceCeedCall(ceed, CeedOperatorSetField(build_op, "geom_data", geom_data_restr,
                                            CEED_BASIS_NONE, CEED_VECTOR_ACTIVE));

  PalaceCeedCall(ceed, CeedOperatorCheckReady(build_op));

  // Compute the quadrature data for the operator.
  PalaceCeedCall(
      ceed, CeedOperatorApply(build_op, mesh_nodes, geom_data, CEED_REQUEST_IMMEDIATE));
  PalaceCeedCall(ceed, CeedOperatorDestroy(&build_op));
}

void AssembleCeedOperator(const CeedQFunctionInfo &info, void *ctx, std::size_t ctx_size,
                          Ceed ceed, CeedElemRestriction trial_restr,
                          CeedElemRestriction test_restr, CeedBasis trial_basis,
                          CeedBasis test_basis, CeedVector geom_data,
                          CeedElemRestriction geom_data_restr, CeedOperator *op)
{
  const auto elements = NonzeroMassElements(info, ctx, ctx_size, ceed, geom_data,
                                             geom_data_restr);
  CeedElemRestriction selected_trial = nullptr, selected_test = nullptr,
                      selected_geom = nullptr;
  if (!elements.empty())
  {
    selected_trial = SelectRestrictionElements(trial_restr, elements);
    if (selected_trial && trial_restr == test_restr)
    {
      PalaceCeedCall(ceed, CeedElemRestrictionReferenceCopy(selected_trial, &selected_test));
    }
    else
    {
      selected_test = SelectRestrictionElements(test_restr, elements);
    }
    selected_geom = SelectRestrictionElements(geom_data_restr, elements);
    if (selected_trial && selected_test && selected_geom)
    {
      trial_restr = selected_trial;
      test_restr = selected_test;
      geom_data_restr = selected_geom;
      const char *trace = std::getenv("PALACE_STAGE_TRACE");
      if (trace && std::strcmp(trace, "1") == 0)
      {
        std::fprintf(stderr, "PALACE_EXACT_ZERO_APPLIED active=%zu assemble_q_data=%d\n",
                     elements.size(), static_cast<int>(info.assemble_q_data));
      }
    }
    // Unsupported layouts conservatively keep the complete original operator.
  }

  // If we are going to be assembling the quadrature data, construct the storage vector for
  // it (to be owned by the operator).
  CeedVector q_data = nullptr;
  CeedElemRestriction q_data_restr = nullptr;
  std::vector<CeedInt> qf_active_sizes;
  if (info.assemble_q_data)
  {
    qf_active_sizes = QuadratureDataSetup(info.trial_ops, ceed, trial_restr, trial_basis,
                                          &q_data, &q_data_restr);
  }

  // Create the QFunction that defines the action of the operator (or its setup).
  CeedQFunction apply_qf;
  PalaceCeedCall(ceed, CeedQFunctionCreateInterior(ceed, 1, info.apply_qf,
                                                   info.apply_qf_path.c_str(), &apply_qf));

  CeedQFunctionContext apply_ctx;
  PalaceCeedCall(ceed, CeedQFunctionContextCreate(ceed, &apply_ctx));
  PalaceCeedCall(ceed, CeedQFunctionContextSetData(apply_ctx, CEED_MEM_HOST,
                                                   CEED_COPY_VALUES, ctx_size, ctx));
  PalaceCeedCall(ceed, CeedQFunctionSetContext(apply_qf, apply_ctx));
  PalaceCeedCall(ceed, CeedQFunctionContextDestroy(&apply_ctx));

  // Inputs/outputs.
  {
    CeedInt geom_data_size;
    PalaceCeedCall(ceed,
                   CeedElemRestrictionGetNumComponents(geom_data_restr, &geom_data_size));
    PalaceCeedCall(
        ceed, CeedQFunctionAddInput(apply_qf, "geom_data", geom_data_size, CEED_EVAL_NONE));
  }
  if (info.trial_ops & EvalMode::Weight)
  {
    PalaceCeedCall(ceed, CeedQFunctionAddInput(apply_qf, "q_w", 1, CEED_EVAL_WEIGHT));
  }
  MFEM_VERIFY(!(info.test_ops & EvalMode::Weight),
              "CeedOperator should not have quadrature weight output!");
  if (!info.assemble_q_data)
  {
    AddQFunctionActiveInputs(info.trial_ops, ceed, trial_basis, apply_qf);
    AddQFunctionActiveOutputs(info.test_ops, ceed, test_basis, apply_qf);
  }
  else
  {
    CeedInt q_data_size;
    PalaceCeedCall(ceed, CeedElemRestrictionGetNumComponents(q_data_restr, &q_data_size));
    PalaceCeedCall(ceed,
                   CeedQFunctionAddOutput(apply_qf, "q_data", q_data_size, CEED_EVAL_NONE));
  }

  // Create the operator.
  PalaceCeedCall(ceed, CeedOperatorCreate(ceed, apply_qf, nullptr, nullptr, op));
  PalaceCeedCall(ceed, CeedQFunctionDestroy(&apply_qf));

  PalaceCeedCall(ceed, CeedOperatorSetField(*op, "geom_data", geom_data_restr,
                                            CEED_BASIS_NONE, geom_data));
  if (info.trial_ops & EvalMode::Weight)
  {
    PalaceCeedCall(ceed, CeedOperatorSetField(*op, "q_w", CEED_ELEMRESTRICTION_NONE,
                                              trial_basis, CEED_VECTOR_NONE));
  }
  if (!info.assemble_q_data)
  {
    AddOperatorActiveInputFields(info.trial_ops, ceed, trial_restr, trial_basis, *op);
    AddOperatorActiveOutputFields(info.test_ops, ceed, test_restr, test_basis, *op);
  }
  else
  {
    PalaceCeedCall(ceed, CeedOperatorSetField(*op, "q_data", q_data_restr, CEED_BASIS_NONE,
                                              CEED_VECTOR_ACTIVE));
  }

  PalaceCeedCall(ceed, CeedOperatorCheckReady(*op));

  // Assemble the quadrature data and create the actual operator.
  if (info.assemble_q_data)
  {
    QuadratureDataAssembly(qf_active_sizes, info, ceed, trial_restr, test_restr,
                           trial_basis, test_basis, q_data, q_data_restr, op);

    // Cleanup (these are now owned by the operator).
    PalaceCeedCall(ceed, CeedElemRestrictionDestroy(&q_data_restr));
    PalaceCeedCall(ceed, CeedVectorDestroy(&q_data));
  }
  PalaceCeedCall(ceed, CeedElemRestrictionDestroy(&selected_trial));
  PalaceCeedCall(ceed, CeedElemRestrictionDestroy(&selected_test));
  PalaceCeedCall(ceed, CeedElemRestrictionDestroy(&selected_geom));
}

void AssembleCeedInterpolator(Ceed ceed, CeedElemRestriction trial_restr,
                              CeedElemRestriction test_restr, CeedBasis interp_basis,
                              CeedOperator *op, CeedOperator *op_t)
{
  // Create the QFunction that defines the action of the operator (only an identity as
  // element dof multiplicity is handled outside of libCEED).
  CeedQFunction apply_qf, apply_qf_t;
  PalaceCeedCall(ceed, CeedQFunctionCreateIdentity(ceed, 1, CEED_EVAL_INTERP,
                                                   CEED_EVAL_NONE, &apply_qf));
  PalaceCeedCall(ceed, CeedQFunctionCreateIdentity(ceed, 1, CEED_EVAL_NONE,
                                                   CEED_EVAL_INTERP, &apply_qf_t));

  // Create the operator.
  PalaceCeedCall(ceed, CeedOperatorCreate(ceed, apply_qf, nullptr, nullptr, op));
  PalaceCeedCall(ceed, CeedQFunctionDestroy(&apply_qf));

  PalaceCeedCall(ceed, CeedOperatorSetField(*op, "input", trial_restr, interp_basis,
                                            CEED_VECTOR_ACTIVE));
  PalaceCeedCall(ceed, CeedOperatorSetField(*op, "output", test_restr, CEED_BASIS_NONE,
                                            CEED_VECTOR_ACTIVE));

  PalaceCeedCall(ceed, CeedOperatorCheckReady(*op));

  // Create the transpose operator.
  PalaceCeedCall(ceed, CeedOperatorCreate(ceed, apply_qf_t, nullptr, nullptr, op_t));
  PalaceCeedCall(ceed, CeedQFunctionDestroy(&apply_qf_t));

  PalaceCeedCall(ceed, CeedOperatorSetField(*op_t, "input", test_restr, CEED_BASIS_NONE,
                                            CEED_VECTOR_ACTIVE));
  PalaceCeedCall(ceed, CeedOperatorSetField(*op_t, "output", trial_restr, interp_basis,
                                            CEED_VECTOR_ACTIVE));

  PalaceCeedCall(ceed, CeedOperatorCheckReady(*op_t));
}

void AssembleCeedElementErrorIntegrator(
    const CeedQFunctionInfo &info, void *ctx, std::size_t ctx_size, Ceed ceed,
    CeedVector input1, CeedVector input2, CeedElemRestriction input1_restr,
    CeedElemRestriction input2_restr, CeedBasis input1_basis, CeedBasis input2_basis,
    CeedElemRestriction mesh_elem_restr, CeedVector geom_data,
    CeedElemRestriction geom_data_restr, CeedOperator *op)
{
  MFEM_VERIFY(!info.assemble_q_data,
              "Quadrature interpolator does not support quadrature data assembly!");

  // Create basis for summing contributions from all quadrature points on the element.
  CeedInt num_qpts;
  PalaceCeedCall(ceed, CeedBasisGetNumQuadraturePoints(input1_basis, &num_qpts));
  CeedBasis mesh_elem_basis;
  {
    // Note: ceed::GetCeedTopology(CEED_TOPOLOGY_LINE) == 1.
    mfem::Vector Bt(num_qpts), Gt(num_qpts), qX(num_qpts), qW(num_qpts);
    Bt = 1.0;
    Gt = 0.0;
    qX = 0.0;
    qW = 0.0;
    PalaceCeedCall(ceed, CeedBasisCreateH1(ceed, CEED_TOPOLOGY_LINE, 1, 1, num_qpts,
                                           Bt.GetData(), Gt.GetData(), qX.GetData(),
                                           qW.GetData(), &mesh_elem_basis));
  }

  // Create the QFunction that defines the action of the operator.
  CeedQFunction apply_qf;
  PalaceCeedCall(ceed, CeedQFunctionCreateInterior(ceed, 1, info.apply_qf,
                                                   info.apply_qf_path.c_str(), &apply_qf));

  CeedQFunctionContext apply_ctx;
  PalaceCeedCall(ceed, CeedQFunctionContextCreate(ceed, &apply_ctx));
  PalaceCeedCall(ceed, CeedQFunctionContextSetData(apply_ctx, CEED_MEM_HOST,
                                                   CEED_COPY_VALUES, ctx_size, ctx));
  PalaceCeedCall(ceed, CeedQFunctionSetContext(apply_qf, apply_ctx));
  PalaceCeedCall(ceed, CeedQFunctionContextDestroy(&apply_ctx));

  // Inputs/outputs. "Test" operations are the operations for the second input vector.
  {
    CeedInt geom_data_size;
    PalaceCeedCall(ceed,
                   CeedElemRestrictionGetNumComponents(geom_data_restr, &geom_data_size));
    PalaceCeedCall(
        ceed, CeedQFunctionAddInput(apply_qf, "geom_data", geom_data_size, CEED_EVAL_NONE));
  }
  if (info.trial_ops & EvalMode::Weight)
  {
    PalaceCeedCall(ceed, CeedQFunctionAddInput(apply_qf, "q_w", 1, CEED_EVAL_WEIGHT));
  }
  AddQFunctionActiveInputs(info.trial_ops, ceed, input1_basis, apply_qf, "u_1");
  AddQFunctionActiveInputs(info.test_ops, ceed, input2_basis, apply_qf, "u_2");
  PalaceCeedCall(ceed, CeedQFunctionAddOutput(apply_qf, "v", 1, CEED_EVAL_INTERP));

  // Create the operator.
  PalaceCeedCall(ceed, CeedOperatorCreate(ceed, apply_qf, nullptr, nullptr, op));
  PalaceCeedCall(ceed, CeedQFunctionDestroy(&apply_qf));

  PalaceCeedCall(ceed, CeedOperatorSetField(*op, "geom_data", geom_data_restr,
                                            CEED_BASIS_NONE, geom_data));
  if (info.trial_ops & EvalMode::Weight)
  {
    PalaceCeedCall(ceed, CeedOperatorSetField(*op, "q_w", CEED_ELEMRESTRICTION_NONE,
                                              input1_basis, CEED_VECTOR_NONE));
  }
  AddOperatorActiveInputFields(info.trial_ops, ceed, input1_restr, input1_basis, *op, "u_1",
                               input1);
  AddOperatorActiveInputFields(info.test_ops, ceed, input2_restr, input2_basis, *op, "u_2",
                               input2);
  PalaceCeedCall(ceed, CeedOperatorSetField(*op, "v", mesh_elem_restr, mesh_elem_basis,
                                            CEED_VECTOR_ACTIVE));

  PalaceCeedCall(ceed, CeedOperatorCheckReady(*op));

  // Cleanup (this is now owned by the operator).
  PalaceCeedCall(ceed, CeedBasisDestroy(&mesh_elem_basis));
}

}  // namespace palace::ceed
