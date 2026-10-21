// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

#include "iterative.hpp"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstddef>
#include <limits>
#include <string>
#include <string_view>
#include "linalg/orthog.hpp"
#include "linalg/basisprefetch.hpp"
#include "utils/communication.hpp"
#include "utils/timer.hpp"
#include "utils/memorymark.hpp"
#include "utils/profilewindow.hpp"

extern "C" void PalaceProfileCapture(int begin) __attribute__((weak));
extern "C" void PalacePCBasisScope(int begin) __attribute__((weak));

namespace palace
{

namespace
{

bool UseStoredBasis()
{
  return std::getenv("PALACE_GMRES_FP32_BASIS");
}

// Diagnostic-only NVTX capture range. Unwind cleanly at its end, without RF output.
class KrylovProfileWindow
{
  int first = -1, count = 0;
  bool active = false, done = false;
  nvtxDomainHandle_t domain = nullptr;
  nvtxStringHandle_t message = nullptr;

public:
  explicit KrylovProfileWindow(MPI_Comm comm)
  {
    const char *raw = std::getenv("PALACE_KRYLOV_PROFILE");
    if (!raw) return;
    const std::string_view value(raw);
    const auto colon = value.find(':');
    MFEM_VERIFY(colon != std::string_view::npos, "Expected profile FIRST:COUNT!");
    const auto begin = value.data(), end = begin + value.size();
    auto a = std::from_chars(begin, begin + colon, first);
    auto b = std::from_chars(begin + colon + 1, end, count);
    MFEM_VERIFY(a.ec == std::errc() && a.ptr == begin + colon && b.ec == std::errc() &&
                    b.ptr == end && first >= 0 && first <= 32 && count >= 2 && count <= 8 &&
                    Mpi::Size(comm) == 1,
                "Profile requires one rank, FIRST=0..32 and COUNT=2..8!");
    domain = nvtxDomainCreateA("palace");
    message = nvtxDomainRegisterStringA(domain, "Krylov sample");
  }

  void Begin(int iteration)
  {
    if (!done && iteration == first)
    {
      MFEM_VERIFY(PalaceProfileSynchronize, "Profile window requires the CUDA adapter sync hook!");
      if (std::getenv("PALACE_PROFILE_CAPTURE_RANGE"))
      {
        MFEM_VERIFY(PalaceProfileCapture, "Selective profile requires the CUDA capture hook!");
        PalaceProfileCapture(1);
      }
      PalaceProfileSynchronize();
      Mpi::Print("PALACE_PROFILE_WINDOW: begin first={} count={}\n", first, count);
      nvtxEventAttributes_t event{};
      event.version = NVTX_VERSION;
      event.size = NVTX_EVENT_ATTRIB_STRUCT_SIZE;
      event.messageType = NVTX_MESSAGE_TYPE_REGISTERED;
      event.message.registered = message;
      nvtxDomainRangePushEx(domain, &event);
      ProfileHostRange("begin", "Krylov sample");
      active = true;
    }
  }

  void End(int iteration)
  {
    if (active) PalaceProfileSynchronize();
    if (active && iteration + 1 == first + count)
    {
      ProfileHostRange("end", "Krylov sample");
      Mpi::Print("PALACE_PROFILE_WINDOW: end first={} count={}\n", first, count);
      nvtxDomainRangePop(domain);
      if (std::getenv("PALACE_PROFILE_CAPTURE_RANGE")) PalaceProfileCapture(0);
      active = false;
      done = true;
      throw KrylovProfileComplete{};
    }
  }

  ~KrylovProfileWindow()
  {
    if (active)
    {
      Mpi::Print("PALACE_PROFILE_WINDOW: incomplete\n");
      nvtxDomainRangePop(domain);
    }
    if (domain) nvtxDomainDestroy(domain);
  }
};

template <typename T>
inline void CheckDot(T dot, const char *msg)
{
  MFEM_ASSERT(std::isfinite(dot) && dot >= 0.0, msg << dot << "!");
}

template <typename T>
inline void CheckDot(std::complex<T> dot, const char *msg)
{
  MFEM_ASSERT(std::isfinite(dot.real()) && std::isfinite(dot.imag()) && dot.real() >= 0.0,
              msg << dot << "!");
}

template <typename T>
inline constexpr T SafeMin()
{
  // Originally part of <T>LAPACK.
  // <T>LAPACK is free software: you can redistribute it and/or modify it under
  // the terms of the BSD 3-Clause license.
  //
  // Copyright (c) 2021-2023, University of Colorado Denver. All rights reserved.
  // Copyright (c) 2017-2021, University of Tennessee. All rights reserved.
  //
  // Original author: Weslley S Pereira, University of Colorado Denver, USA
  constexpr int fradix = std::numeric_limits<T>::radix;
  constexpr int expm = std::numeric_limits<T>::min_exponent;
  constexpr int expM = std::numeric_limits<T>::max_exponent;
  // Note: pow is not constexpr in C++17 so this actually might not return a constexpr for
  // all compilers.
  return std::max(std::pow(fradix, T(expm - 1)), std::pow(fradix, T(1 - expM)));
}

template <typename T>
inline constexpr T SafeMax()
{
  // Originally part of <T>LAPACK.
  // <T>LAPACK is free software: you can redistribute it and/or modify it under
  // the terms of the BSD 3-Clause license.
  //
  // Copyright (c) 2021-2023, University of Colorado Denver. All rights reserved.
  // Copyright (c) 2017-2021, University of Tennessee. All rights reserved.
  //
  // Original author: Weslley S Pereira, University of Colorado Denver, USA
  constexpr int fradix = std::numeric_limits<T>::radix;
  constexpr int expm = std::numeric_limits<T>::min_exponent;
  constexpr int expM = std::numeric_limits<T>::max_exponent;
  // Note: pow is not constexpr in C++17 so this actually might not return a constexpr for
  // all compilers.
  return std::min(std::pow(fradix, T(1 - expm)), std::pow(fradix, T(expM - 1)));
}

template <typename T>
inline void GeneratePlaneRotation(const T dx, const T dy, T &cs, T &sn)
{
  // See LAPACK's s/dlartg.
  const T safmin = SafeMin<T>();
  const T safmax = SafeMax<T>();
  const T root_min = std::sqrt(safmin);
  const T root_max = std::sqrt(safmax / 2);
  if (dy == 0.0)
  {
    cs = 1.0;
    sn = 0.0;
    return;
  }
  if (dx == 0.0)
  {
    cs = 0.0;
    sn = std::copysign(1.0, dy);
    return;
  }
  T dx1 = std::abs(dx);
  T dy1 = std::abs(dy);
  if (dx1 > root_min && dx1 < root_max && dy1 > root_min && dy1 < root_max)
  {
    T d = std::sqrt(dx * dx + dy * dy);
    cs = dx1 / d;
    sn = dy / std::copysign(d, dx);
  }
  else
  {
    T u = std::min(safmax, std::max(safmin, std::max(dx1, dy1)));
    T dxs = dx / u;
    T dys = dy / u;
    T d = std::sqrt(dxs * dxs + dys * dys);
    cs = std::abs(dxs) / d;
    sn = dys / std::copysign(d, dx);
  }
}

template <typename T>
inline void GeneratePlaneRotation(const std::complex<T> dx, const std::complex<T> dy, T &cs,
                                  std::complex<T> &sn)
{
  // Generates a plane rotation so that:
  //   [  cs        sn ] [ dx ]  =  [ r ]
  //   [ -conj(sn)  cs ] [ dy ]     [ 0 ]
  // where cs is real and cs² + |sn|² = 1. See LAPACK's c/zlartg.
  const T safmin = SafeMin<T>();
  const T safmax = SafeMax<T>();
  if (dy == 0.0)
  {
    cs = 1.0;
    sn = 0.0;
    return;
  }
  if (dx == 0.0)
  {
    cs = 0.0;
    if (dy.real() == 0.0)
    {
      sn = std::conj(dy) / std::abs(dy.imag());
    }
    else if (dy.imag() == 0.0)
    {
      sn = std::conj(dy) / std::abs(dy.real());
    }
    else
    {
      const T root_min = std::sqrt(safmin);
      const T root_max = std::sqrt(safmax / 2);
      T dy1 = std::max(std::abs(dy.real()), std::abs(dy.imag()));
      if (dy1 > root_min && dy1 < root_max)
      {
        sn = std::conj(dy) / std::sqrt(dy.real() * dy.real() + dy.imag() * dy.imag());
      }
      else
      {
        T u = std::min(safmax, std::max(safmin, dy1));
        std::complex<T> dys = dy / u;
        sn = std::conj(dys) / std::sqrt(dys.real() * dys.real() + dys.imag() * dys.imag());
      }
    }
    return;
  }
  const T root_min = std::sqrt(safmin);
  const T root_max = std::sqrt(safmax / 4);
  T dx1 = std::max(std::abs(dx.real()), std::abs(dx.imag()));
  T dy1 = std::max(std::abs(dy.real()), std::abs(dy.imag()));
  if (dx1 > root_min && dx1 < root_max && dy1 > root_min && dy1 < root_max)
  {
    T dx2 = dx.real() * dx.real() + dx.imag() * dx.imag();
    T dy2 = dy.real() * dy.real() + dy.imag() * dy.imag();
    T dz2 = dx2 + dy2;
    if (dx2 >= dz2 * safmin)
    {
      cs = std::sqrt(dx2 / dz2);
      if (dx2 > root_min && dz2 < root_max * 2)
      {
        sn = std::conj(dy) * (dx / std::sqrt(dx2 * dz2));
      }
      else
      {
        sn = std::conj(dy) * ((dx / cs) / dz2);
      }
    }
    else
    {
      T d = std::sqrt(dx2 * dz2);
      cs = dx2 / d;
      sn = std::conj(dy) * (dx / d);
    }
  }
  else
  {
    T u = std::min(safmax, std::max(safmin, std::max(dx1, dy1))), w;
    std::complex<T> dys = dy / u, dxs;
    T dy2 = dys.real() * dys.real() + dys.imag() * dys.imag(), dx2, dz2;
    if (dx1 / u < root_min)
    {
      T v = std::min(safmax, std::max(safmin, dx1));
      w = v / u;
      dxs = dx / v;
      dx2 = dxs.real() * dxs.real() + dxs.imag() * dxs.imag();
      dz2 = dx2 * w * w + dy2;
    }
    else
    {
      w = 1.0;
      dxs = dx / u;
      dx2 = dxs.real() * dxs.real() + dxs.imag() * dxs.imag();
      dz2 = dx2 + dy2;
    }
    if (dx2 >= dz2 * safmin)
    {
      cs = std::sqrt(dx2 / dz2);
      if (dx2 > root_min && dz2 < root_max * 2)
      {
        sn = std::conj(dys) * (dxs / std::sqrt(dx2 * dz2));
      }
      else
      {
        sn = std::conj(dys) * ((dxs / cs) / dz2);
      }
    }
    else
    {
      T d = std::sqrt(dx2 * dz2);
      cs = dx2 / d;
      sn = std::conj(dys) * (dxs / d);
    }
    cs *= w;
  }
}

template <typename T>
inline void ApplyPlaneRotation(T &dx, T &dy, const T cs, const T sn)
{
  T t = cs * dx + sn * dy;
  dy = -sn * dx + cs * dy;
  dx = t;
}

template <typename T>
inline void ApplyPlaneRotation(std::complex<T> &dx, std::complex<T> &dy, const T cs,
                               const std::complex<T> sn)
{
  std::complex<T> t = cs * dx + sn * dy;
  dy = -std::conj(sn) * dx + cs * dy;
  dx = t;
}

template <typename OperType, typename VecType>
inline void ApplyB(const Solver<OperType> *B, const VecType &x, VecType &y,
                   bool use_timer = true)
{
  BlockTimer bt(Timer::KSP_PRECONDITIONER, use_timer);
  MFEM_ASSERT(B, "Missing preconditioner in ApplyB!");
  struct PCScope
  {
    bool enabled;
    PCScope()
    {
      static const bool on = [] {
        const char *value = std::getenv("PALACE_PC_BASIS_FP32_FORWARD");
        return value && std::string_view(value) == "1";
      }();
      enabled = on;
      if (enabled)
      {
        MFEM_VERIFY(PalacePCBasisScope, "Mixed PC basis requires its runtime adapter!");
        PalacePCBasisScope(1);
      }
    }
    ~PCScope() { if (enabled) PalacePCBasisScope(0); }
  } scope;
  B->Mult(x, y);
}

template <typename OperType, typename VecType>
inline void InitialResidual(PreconditionerSide side, const OperType *A,
                            const Solver<OperType> *B, const VecType &b, VecType &x,
                            VecType &r, VecType &z, bool initial_guess,
                            bool use_timer = true)
{
  if (B && side == PreconditionerSide::LEFT)
  {
    if (initial_guess)
    {
      A->Mult(x, z);
      linalg::AXPBY(1.0, b, -1.0, z);
      ApplyB(B, z, r, use_timer);
    }
    else
    {
      ApplyB(B, b, r, use_timer);
      x = 0.0;
    }
  }
  else  // !B || side == PreconditionerSide::RIGHT
  {
    if (initial_guess)
    {
      A->Mult(x, r);
      linalg::AXPBY(1.0, b, -1.0, r);
    }
    else
    {
      r = b;
      x = 0.0;
    }
  }
}

template <typename OperType, typename VecType>
inline void ApplyBA(PreconditionerSide side, const OperType *A, const Solver<OperType> *B,
                    const VecType &x, VecType &y, VecType &z, bool use_timer = true)
{
  if (B && side == PreconditionerSide::LEFT)
  {
    A->Mult(x, z);
    ApplyB(B, z, y, use_timer);
  }
  else if (B && side == PreconditionerSide::RIGHT)
  {
    ApplyB(B, x, z, use_timer);
    A->Mult(z, y);
  }
  else
  {
    A->Mult(x, y);
  }
}

}  // namespace

template <typename OperType>
IterativeSolver<OperType>::IterativeSolver(MPI_Comm comm, int print)
  : Solver<OperType>(), comm(comm), A(nullptr), B(nullptr)
{
  print_opts.Warnings();
  if (print > 0)
  {
    print_opts.Summary();
    if (print > 1)
    {
      print_opts.Iterations();
      if (print > 2)
      {
        print_opts.All();
      }
    }
  }
  int_width = 3;
  tab_width = 0;

  rel_tol = abs_tol = 0.0;
  max_it = 100;

  converged = false;
  initial_res = 1.0;
  final_res = 0.0;
  final_it = 0;

  use_timer = false;
}

template <typename OperType>
void CgSolver<OperType>::Mult(const VecType &b, VecType &x) const
{
  // Set up workspace.
  ScalarType beta, beta_prev = 0.0, alpha, denom;
  RealType res, eps;
  MFEM_VERIFY(A, "Operator must be set for CgSolver::Mult!");
  MFEM_ASSERT(A->Width() == x.Size() && A->Height() == b.Size(),
              "Size mismatch for CgSolver::Mult!");
  r.SetSize(A->Height());
  z.SetSize(A->Height());
  p.SetSize(A->Height());
  r.UseDevice(true);
  z.UseDevice(true);
  p.UseDevice(true);

  // Initialize.
  if (this->initial_guess)
  {
    A->Mult(x, r);
    linalg::AXPBY(1.0, b, -1.0, r);
  }
  else
  {
    r = b;
    x = 0.0;
  }
  if (B)
  {
    ApplyB(B, r, z, this->use_timer);
  }
  else
  {
    z = r;
  }
  beta = linalg::Dot(comm, z, r);
  CheckDot(beta, "PCG preconditioner is not positive definite: (Br, r) = ");
  res = std::sqrt(std::abs(beta));
  if (this->initial_guess)
  {
    ScalarType beta_rhs;
    if (B)
    {
      ApplyB(B, b, p, this->use_timer);
      beta_rhs = linalg::Dot(comm, p, b);
    }
    else
    {
      beta_rhs = linalg::Norml2(comm, b);
    }
    CheckDot(beta_rhs, "PCG preconditioner is not positive definite: (Bb, b) = ");
    initial_res = std::sqrt(std::abs(beta_rhs));
  }
  else
  {
    initial_res = res;
  }
  eps = std::max(rel_tol * initial_res, abs_tol);
  converged = (res < eps);

  // Begin iterations.
  int it = 0;
  if (print_opts.iterations)
  {
    Mpi::Print(comm, "{}Residual norms for PCG solve\n",
               std::string(tab_width + int_width - 1, ' '));
  }
  for (; it < max_it && !converged; it++)
  {
    if (print_opts.iterations)
    {
      Mpi::Print(comm, "{}{:{}d} KSP residual norm ||r||_B = {:.6e}\n",
                 std::string(tab_width, ' '), it, int_width, res);
    }
    if (!it)
    {
      p = z;
    }
    else
    {
      linalg::AXPBY(ScalarType(1.0), z, beta / beta_prev, p);
    }

    A->Mult(p, z);
    denom = linalg::Dot(comm, z, p);
    CheckDot(denom, "PCG operator is not positive definite: (Ap, p) = ");
    alpha = beta / denom;

    x.Add(alpha, p);
    r.Add(-alpha, z);

    beta_prev = beta;
    if (B)
    {
      ApplyB(B, r, z, this->use_timer);
    }
    else
    {
      z = r;
    }
    beta = linalg::Dot(comm, z, r);
    CheckDot(beta, "PCG preconditioner is not positive definite: (Br, r) = ");
    res = std::sqrt(std::abs(beta));
    converged = (res < eps);
  }
  if (print_opts.iterations)
  {
    Mpi::Print(comm, "{}{:{}d} KSP residual norm ||r||_B = {:.6e}\n",
               std::string(tab_width, ' '), it, int_width, res);
  }
  if (print_opts.summary || (print_opts.warnings && eps > 0.0 && !converged))
  {
    Mpi::Print(comm, "{}PCG solver {} in {:d} iteration{}", std::string(tab_width, ' '),
               converged ? "converged" : "did NOT converge", it, (it == 1) ? "" : "s");
    if (it > 0)
    {
      Mpi::Print(comm, " (avg. reduction factor: {:.3e})\n",
                 std::pow(res / initial_res, 1.0 / it));
    }
    else
    {
      Mpi::Print(comm, "\n");
    }
  }
  final_res = res;
  final_it = it;
}

template <typename OperType>
void GmresSolver<OperType>::Initialize() const
{
  if (!V.empty())
  {
    MFEM_ASSERT(V.size() == static_cast<std::size_t>(max_dim + 1) &&
                    V[0].Size() == A->Height(),
                "Repeated solves with GmresSolver should not modify the operator size or "
                "restart dimension!");
    return;
  }
  if (max_dim < 0)
  {
    max_dim = max_it;
  }
  constexpr int init_size = 5;
  V.resize(max_dim + 1);
  for (int j = 0; j < std::min(UseStoredBasis() ? 1 : init_size, max_dim + 1); j++)
  {
    V[j].SetSize(A->Height());
    V[j].UseDevice(true);
  }
  // H, s, cs, sn are allocated incrementally in Update() to avoid O(max_dim^2) upfront
  // cost when max_dim is large (e.g., defaulting to max_it).
  s.resize(std::min(init_size + 1, max_dim + 1));
  cs.resize(std::min(init_size + 1, max_dim + 1));
  sn.resize(std::min(init_size + 1, max_dim + 1));
  H.resize(static_cast<std::size_t>(max_dim + 1) * std::min(init_size, max_dim));
}

template <typename OperType>
void GmresSolver<OperType>::Update(int j) const
{
  // Add storage for basis vectors, Hessenberg columns, and rotations in increments.
  constexpr int add_size = 10;
  for (int k = j + 1; !UseStoredBasis() && k < std::min(j + 1 + add_size, max_dim + 1); k++)
  {
    V[k].SetSize(A->Height());
    V[k].UseDevice(true);
  }
  int needed_cols = std::min(j + 1 + add_size, max_dim);
  int current_cols = static_cast<int>(H.size()) / (max_dim + 1);
  if (needed_cols > current_cols)
  {
    H.resize(static_cast<std::size_t>(max_dim + 1) * needed_cols);
  }
  auto needed_size = static_cast<std::size_t>(std::min(j + 2 + add_size, max_dim + 1));
  if (needed_size > s.size())
  {
    s.resize(needed_size);
    cs.resize(needed_size);
    sn.resize(needed_size);
  }
}

template <typename OperType>
void GmresSolver<OperType>::Mult(const VecType &b, VecType &x) const
{
  KrylovProfileWindow profile_window(comm);
  // Set up workspace.
  RealType beta = 0.0, true_beta, eps = 0.0;
  MFEM_VERIFY(A, "Operator must be set for GmresSolver::Mult!");
  MFEM_ASSERT(A->Width() == x.Size() && A->Height() == b.Size(),
              "Size mismatch for GmresSolver::Mult!");
  r.SetSize(A->Height());
  r.UseDevice(true);
  Initialize();
  const bool compressed_basis = UseStoredBasis();
  const bool direct_basis = std::getenv("PALACE_GMRES_FP32_DIRECT") != nullptr;
  const bool prefetch_basis = std::getenv("PALACE_GMRES_BASIS_PREFETCH") != nullptr;
  MFEM_VERIFY(!prefetch_basis || direct_basis, "Basis prefetch requires direct FP32 basis!");
  const auto prefetch_begin = GetBasisPrefetchStats();
  MFEM_VERIFY(!direct_basis || compressed_basis, "Direct basis requires PALACE_GMRES_FP32_BASIS!");
  MFEM_VERIFY(!compressed_basis || gs_orthog == Orthogonalization::MGS,
              "FP32 basis pilot currently supports MGS GMRES only!");
  std::vector<StoredBasisVector> packed_basis(compressed_basis ? max_dim + 1 : 0);
  VecType basis_read;
  VecType basis_partial;
  if (compressed_basis)
  {
    basis_read.SetSize(A->Height());
    basis_read.UseDevice(true);
    Mpi::Print(comm, "PALACE_STORED_BASIS: storage=FP32 RAM/VRAM, FP64 arithmetic; K={:d}, direct={}\n",
               max_dim, direct_basis);
  }

  const auto report_residual = [&](RealType checked_beta)
  {
    Mpi::Print(comm, "PALACE_KSP_CHECK: absolute={:.12e} relative_initial={:.12e} threshold={:.12e}\n",
               checked_beta, checked_beta / initial_res, eps);
    if (std::getenv("PALACE_VERIFY_RESIDUAL"))
    {
      // LEFT GMRES stops on ||B(b-Ax)||, which need not control ||b-Ax||.
      // Reuse scratch vectors; this diagnostic does not change the stopping rule.
      // The action-relative measure below is NOT a normwise backward error:
      // ||Ax|| is not ||A||*||x||. Report the constituent norms explicitly.
      A->Mult(x, V[0]);
      const auto ax_norm = linalg::Norml2(comm, V[0]);
      r = b;
      r -= V[0];
      const auto raw_norm = linalg::Norml2(comm, r);
      const auto rhs_norm = linalg::Norml2(comm, b);
      const auto relative_rhs = rhs_norm > 0.0 ? raw_norm / rhs_norm :
                                (raw_norm == 0.0 ? 0.0 : std::numeric_limits<double>::infinity());
      const auto denominator = ax_norm + rhs_norm;
      const auto relative_action = denominator > 0.0 ? raw_norm / denominator :
                                   (raw_norm == 0.0 ? 0.0 : std::numeric_limits<double>::infinity());
      Mpi::Print(comm,
                 "PALACE_RAW_RESIDUAL: pc_side={} raw={:.12e} rhs={:.12e} "
                 "ax={:.12e} relative_rhs={:.12e} relative_action={:.12e}\n",
                 !B ? "none" : (pc_side == PreconditionerSide::LEFT ? "left" : "right"),
                 raw_norm, rhs_norm, ax_norm, relative_rhs, relative_action);
    }
  };

  // Begin iterations.
  converged = false;
  int it = 0, restart = 0;
  if (print_opts.iterations)
  {
    Mpi::Print(comm, "{}Residual norms for GMRES solve\n",
               std::string(tab_width + int_width - 1, ' '));
  }
  for (; it < max_it; restart++)
  {
    // Initialize.
    InitialResidual(pc_side, A, B, b, x, r, V[0], (this->initial_guess || restart > 0),
                    this->use_timer);
    true_beta = linalg::Norml2(comm, r);
    CheckDot(true_beta, "GMRES residual norm is not valid: beta = ");
    if (it == 0)
    {
      if (this->initial_guess)
      {
        RealType beta_rhs;
        if (B && pc_side == PreconditionerSide::LEFT)
        {
          ApplyB(B, b, V[0], this->use_timer);
          beta_rhs = linalg::Norml2(comm, V[0]);
        }
        else  // !B || pc_side == PreconditionerSide::RIGHT
        {
          beta_rhs = linalg::Norml2(comm, b);
        }
        CheckDot(beta_rhs, "GMRES residual norm is not valid: beta_rhs = ");
        initial_res = beta_rhs;
      }
      else
      {
        initial_res = true_beta;
      }
      eps = std::max(rel_tol * initial_res, abs_tol);
    }
    else if (beta > 0.0 && std::abs(beta - true_beta) > 0.1 * true_beta &&
             print_opts.warnings)
    {
      Mpi::Print(
          comm,
          "{}GMRES residual at restart ({:.6e}) is far from the residual norm estimate "
          "from the recursion formula ({:.6e}) (initial residual = {:.6e})\n",
          std::string(tab_width, ' '), true_beta, beta, initial_res);
    }
    beta = true_beta;
    if (beta < eps)
    {
      // A verified initial guess may need no Arnoldi iterations. Report its check too.
      if (compressed_basis || std::getenv("PALACE_VERIFY_RESIDUAL")) report_residual(beta);
      converged = true;
      break;
    }

    V[0] = 0.0;
    V[0].Add(1.0 / beta, r);
    if (compressed_basis) packed_basis[0].Pack(V[0]);
    std::fill(s.begin(), s.end(), 0.0);
    s[0] = beta;

    int j = 0;
    for (;; j++, it++)
    {
      profile_window.Begin(it);
      if (print_opts.iterations)
      {
        Mpi::Print(comm, "{}{:{}d} (restart {:d}) KSP residual norm {:.6e}\n",
                   std::string(tab_width, ' '), it, int_width, restart, beta);
      }
      VecType &w = compressed_basis ? V[0] : V[j + 1];
      if ((!compressed_basis && w.Size() == 0) ||
          (compressed_basis && H.size() < static_cast<std::size_t>((j + 1) * (max_dim + 1))))
      {
        Update(j);
      }
      if (compressed_basis)
      {
        packed_basis[j].Unpack(basis_read);
        ApplyBA(pc_side, A, B, basis_read, w, r, this->use_timer);
      }
      else ApplyBA(pc_side, A, B, V[j], w, r, this->use_timer);

      ScalarType *Hj = H.data() + j * (max_dim + 1);
      const bool trace_orthog = std::getenv("PALACE_PHASE_TRACE") != nullptr;
      if (trace_orthog)
      {
        nvtxRangePushA("Krylov orthogonalization");
        ProfileHostRange("begin", "Krylov orthogonalization");
      }
      if (compressed_basis)
      {
        for (int k = 0; k <= j; k++)
        {
          if (direct_basis)
          {
            Hj[k] = packed_basis[k].Dot(comm, w, basis_partial);
            packed_basis[k].AddTo(-Hj[k], w);
          }
          else
          {
            packed_basis[k].Unpack(basis_read);
            Hj[k] = linalg::Dot(comm, w, basis_read);
            w.Add(-Hj[k], basis_read);
          }
        }
      }
      else linalg::OrthogonalizeColumn(gs_orthog, comm, V, w, Hj, j + 1);
      if (trace_orthog)
      {
        ProfileHostRange("end", "Krylov orthogonalization");
        nvtxRangePop();
      }
      Hj[j + 1] = linalg::Norml2(comm, w);
      w *= 1.0 / Hj[j + 1];
      if (compressed_basis) packed_basis[j + 1].Pack(w);

      for (int k = 0; k < j; k++)
      {
        ApplyPlaneRotation(Hj[k], Hj[k + 1], cs[k], sn[k]);
      }
      GeneratePlaneRotation(Hj[j], Hj[j + 1], cs[j], sn[j]);
      ApplyPlaneRotation(Hj[j], Hj[j + 1], cs[j], sn[j]);
      ApplyPlaneRotation(s[j], s[j + 1], cs[j], sn[j]);

      beta = std::abs(s[j + 1]);
      CheckDot(beta, "GMRES residual norm is not valid: beta = ");
      profile_window.End(it);
      converged = (beta < eps);
      if (converged || j + 1 == max_dim || it + 1 == max_it)
      {
        it++;
        break;
      }
    }

    // Reconstruct the solution (for restart or due to convergence or maximum iterations).
    for (int i = j; i >= 0; i--)
    {
      ScalarType *Hi = H.data() + i * (max_dim + 1);
      s[i] /= Hi[i];
      for (int k = i - 1; k >= 0; k--)
      {
        s[k] -= Hi[k] * s[i];
      }
    }
    if (!B || pc_side == PreconditionerSide::LEFT)
    {
      for (int k = 0; k <= j; k++)
      {
        if (compressed_basis)
        {
          if (direct_basis) packed_basis[k].AddTo(s[k], x);
          else
          {
            packed_basis[k].Unpack(basis_read);
            x.Add(s[k], basis_read);
          }
        }
        else x.Add(s[k], V[k]);
      }
    }
    else  // B && pc_side == PreconditionerSide::RIGHT
    {
      r = 0.0;
      for (int k = 0; k <= j; k++)
      {
        if (compressed_basis)
        {
          if (direct_basis) packed_basis[k].AddTo(s[k], r);
          else
          {
            packed_basis[k].Unpack(basis_read);
            r.Add(s[k], basis_read);
          }
        }
        else r.Add(s[k], V[k]);
      }
      ApplyB(B, r, V[0], this->use_timer);
      x += V[0];
    }
    if (converged && (compressed_basis || std::getenv("PALACE_VERIFY_RESIDUAL")))
    {
      // Recompute the actual stopping norm, not only the Arnoldi recurrence.
      // Float basis storage can introduce a residual gap on ill-conditioned FEM.
      InitialResidual(pc_side, A, B, b, x, r, V[0], true, this->use_timer);
      const auto checked_beta = linalg::Norml2(comm, r);
      CheckDot(checked_beta, "Verified GMRES residual is not valid: ");
      report_residual(checked_beta);
      beta = checked_beta;
      converged = beta < eps;
      if (!converged)
        Mpi::Print(comm, "PALACE_RELIABLE_RESTART: verified stopping residual gap\n");
    }
    if (converged)
    {
      break;
    }
  }
  if (print_opts.iterations)
  {
    Mpi::Print(comm, "{}{:{}d} (restart {:d}) KSP residual norm {:.6e}\n",
               std::string(tab_width, ' '), it, int_width, restart, beta);
  }
  if (std::getenv("PALACE_VERIFY_RESIDUAL"))
  {
    A->Mult(x, r);
    r.Add(-1.0, b);
    auto nr = linalg::Norml2(comm, r);
    auto nb = linalg::Norml2(comm, b);
    Mpi::Print(comm, "PALACE_TRUE_RESIDUAL: norm_Ax_minus_b={:.12e} norm_b={:.12e} relative={:.12e}\n",
               nr, nb, nr / std::max(nb, std::numeric_limits<RealType>::min()));
  }
  if (print_opts.summary || (print_opts.warnings && eps > 0.0 && !converged))
  {
    Mpi::Print(comm, "{}GMRES solver {} in {:d} iteration{}", std::string(tab_width, ' '),
               converged ? "converged" : "did NOT converge", it, (it == 1) ? "" : "s");
    if (it > 0)
    {
      Mpi::Print(comm, " (avg. reduction factor: {:.3e})\n",
                 std::pow(beta / initial_res, 1.0 / it));
    }
    else
    {
      Mpi::Print(comm, "\n");
    }
  }
  final_res = beta;
  final_it = it;
  if (prefetch_basis)
  {
    const auto stats = GetBasisPrefetchStats();
    Mpi::Print(comm, "PALACE_BASIS_PREFETCH: managed=true stream=0 calls={:d} requested_bytes={:d}\n",
               stats.calls - prefetch_begin.calls, stats.bytes - prefetch_begin.bytes);
  }
  if (std::getenv("PALACE_RELEASE_GMRES_BASIS"))
  {
    MemoryMark("gmres.basis_release.begin");
    std::size_t bytes = 0, count = 0;
    for (const auto &v : V)
    {
      bytes += static_cast<std::size_t>(v.Size()) * sizeof(ScalarType);
      count += v.Size() > 0;
    }
    V.clear();  // Discard capacity in each owning vector, not the solution or restart data.
    if (Mpi::Root(comm))
    {
      // Keep the complete diagnostic on the same stream as the memory phase markers.
      std::fprintf(stderr,
                   "PALACE_GMRES_BASIS_RELEASED: vectors=%zu logical_fp64_bytes=%zu\n",
                   count, bytes);
    }
    MemoryMark("gmres.basis_release.end");
  }
}

template <typename OperType>
void FgmresSolver<OperType>::Initialize() const
{
  GmresSolver<OperType>::Initialize();
  constexpr int init_size = 5;
  Z.resize(max_dim + 1);
  for (int j = 0; j < std::min(UseStoredBasis() ? 1 : init_size, max_dim + 1); j++)
  {
    Z[j].SetSize(A->Height());
    Z[j].UseDevice(true);
  }
}

template <typename OperType>
void FgmresSolver<OperType>::Update(int j) const
{
  // Add storage for basis vectors in increments.
  GmresSolver<OperType>::Update(j);
  constexpr int add_size = 10;
  for (int k = j + 1; !UseStoredBasis() && k < std::min(j + 1 + add_size, max_dim + 1); k++)
  {
    Z[k].SetSize(A->Height());
    Z[k].UseDevice(true);
  }
}

template <typename OperType>
void FgmresSolver<OperType>::Mult(const VecType &b, VecType &x) const
{
  MFEM_VERIFY(!UseStoredBasis(),
              "FP32 basis pilot does not support FGMRES!");
  // Set up workspace.
  RealType beta = 0.0, true_beta, eps = 0.0;
  MFEM_VERIFY(A && B, "Operator and preconditioner must be set for FgmresSolver::Mult!");
  MFEM_ASSERT(A->Width() == x.Size() && A->Height() == b.Size(),
              "Size mismatch for FgmresSolver::Mult!");
  Initialize();

  // Begin iterations.
  converged = false;
  int it = 0, restart = 0;
  if (print_opts.iterations)
  {
    Mpi::Print(comm, "{}Residual norms for FGMRES solve\n",
               std::string(tab_width + int_width - 1, ' '));
  }
  for (; it < max_it; restart++)
  {
    // Initialize.
    InitialResidual(PreconditionerSide::RIGHT, A, B, b, x, Z[0], V[0],
                    (this->initial_guess || restart > 0), this->use_timer);
    true_beta = linalg::Norml2(comm, Z[0]);
    CheckDot(true_beta, "FGMRES residual norm is not valid: beta = ");
    if (it == 0)
    {
      if (this->initial_guess)
      {
        auto beta_rhs = linalg::Norml2(comm, b);
        CheckDot(beta_rhs, "GMRES residual norm is not valid: beta_rhs = ");
        initial_res = beta_rhs;
      }
      else
      {
        initial_res = true_beta;
      }
      eps = std::max(rel_tol * initial_res, abs_tol);
    }
    else if (beta > 0.0 && std::abs(beta - true_beta) > 0.1 * true_beta &&
             print_opts.warnings)
    {
      Mpi::Print(
          comm,
          "{}FGMRES residual at restart ({:.6e}) is far from the residual norm estimate "
          "from the recursion formula ({:.6e}) (initial residual = {:.6e})\n",
          std::string(tab_width, ' '), true_beta, beta, initial_res);
    }
    beta = true_beta;
    if (beta < eps)
    {
      converged = true;
      break;
    }

    V[0] = 0.0;
    V[0].Add(1.0 / beta, Z[0]);
    std::fill(s.begin(), s.end(), 0.0);
    s[0] = beta;

    int j = 0;
    for (;; j++, it++)
    {
      if (print_opts.iterations)
      {
        Mpi::Print(comm, "{}{:{}d} (restart {:d}) KSP residual norm {:.6e}\n",
                   std::string(tab_width, ' '), it, int_width, restart, beta);
      }
      VecType &w = V[j + 1];
      if (w.Size() == 0)
      {
        Update(j);
      }
      ApplyBA(PreconditionerSide::RIGHT, A, B, V[j], w, Z[j], this->use_timer);

      ScalarType *Hj = H.data() + j * (max_dim + 1);
      const bool trace_orthog = std::getenv("PALACE_PHASE_TRACE") != nullptr;
      if (trace_orthog) nvtxRangePushA("Krylov orthogonalization");
      linalg::OrthogonalizeColumn(gs_orthog, comm, V, w, Hj, j + 1);
      if (trace_orthog) nvtxRangePop();
      Hj[j + 1] = linalg::Norml2(comm, w);
      w *= 1.0 / Hj[j + 1];

      for (int k = 0; k < j; k++)
      {
        ApplyPlaneRotation(Hj[k], Hj[k + 1], cs[k], sn[k]);
      }
      GeneratePlaneRotation(Hj[j], Hj[j + 1], cs[j], sn[j]);
      ApplyPlaneRotation(Hj[j], Hj[j + 1], cs[j], sn[j]);
      ApplyPlaneRotation(s[j], s[j + 1], cs[j], sn[j]);

      beta = std::abs(s[j + 1]);
      CheckDot(beta, "FGMRES residual norm is not valid: beta = ");
      converged = (beta < eps);
      if (converged || j + 1 == max_dim || it + 1 == max_it)
      {
        it++;
        break;
      }
    }

    // Reconstruct the solution (for restart or due to convergence or maximum iterations).
    for (int i = j; i >= 0; i--)
    {
      ScalarType *Hi = H.data() + i * (max_dim + 1);
      s[i] /= Hi[i];
      for (int k = i - 1; k >= 0; k--)
      {
        s[k] -= Hi[k] * s[i];
      }
    }
    for (int k = 0; k <= j; k++)
    {
      x.Add(s[k], Z[k]);
    }
    if (converged)
    {
      break;
    }
  }
  if (print_opts.iterations)
  {
    Mpi::Print(comm, "{}{:{}d} (restart {:d}) KSP residual norm {:.6e}\n",
               std::string(tab_width, ' '), it, int_width, restart, beta);
  }
  if (print_opts.summary || (print_opts.warnings && eps > 0.0 && !converged))
  {
    Mpi::Print(comm, "{}FGMRES solver {} in {:d} iteration{}", std::string(tab_width, ' '),
               converged ? "converged" : "did NOT converge", it, (it == 1) ? "" : "s");
    if (it > 0)
    {
      Mpi::Print(comm, " (avg. reduction factor: {:.3e})\n",
                 std::pow(beta / initial_res, 1.0 / it));
    }
    else
    {
      Mpi::Print(comm, "\n");
    }
  }
  final_res = beta;
  final_it = it;
}

template class IterativeSolver<Operator>;
template class IterativeSolver<ComplexOperator>;
template class CgSolver<Operator>;
template class CgSolver<ComplexOperator>;
template class GmresSolver<Operator>;
template class GmresSolver<ComplexOperator>;
template class FgmresSolver<Operator>;
template class FgmresSolver<ComplexOperator>;

}  // namespace palace
