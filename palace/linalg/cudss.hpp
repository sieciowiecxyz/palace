// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#ifndef PALACE_LINALG_CUDSS_HPP
#define PALACE_LINALG_CUDSS_HPP

#include <mfem.hpp>

#if defined(MFEM_USE_CUDSS)

#include "linalg/solver.hpp"
#include "utils/labels.hpp"

namespace palace
{

//
// A wrapper for cuDSS.
//
class CuDSSSolver : public mfem::CuDSSSolver
{
public:
  CuDSSSolver(MPI_Comm comm, MatrixSymmetry sym, SymbolicFactorization reorder,
              bool reorder_reuse, int print);

  void SetReorderReuse(bool reorder_reuse);
};

// Experimental single-rank FP64 complex coarse solve without a real 2N block.
// The default MfemWrapperSolver path remains separate.
class ComplexCuDSSSolver final : public Solver<ComplexOperator>
{
  struct Impl;
  std::unique_ptr<Impl> impl;
  bool drop_small_entries;

public:
  ComplexCuDSSSolver(MPI_Comm comm, bool drop_small_entries);
  ~ComplexCuDSSSolver() override;
  void SetOperator(const ComplexOperator &op) override;
  void Mult(const ComplexVector &x, ComplexVector &y) const override;
};

}  // namespace palace

#endif

#endif  // PALACE_LINALG_CUDSS_HPP
