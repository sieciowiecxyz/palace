// SPDX-License-Identifier: Apache-2.0
// Actual exported Palace vector methods, not a replacement CUDA implementation.
#include <algorithm>
#include <chrono>
#include <complex>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <type_traits>
#include <vector>
#include <sys/resource.h>
#include <nlohmann/json.hpp>
#include "linalg/hypre.hpp"
#include "linalg/vector.hpp"

using namespace palace;
using json = nlohmann::json;
namespace
{
void Fill(Vector &x, unsigned int seed)
{
  std::mt19937 generator(seed);
  std::normal_distribution<double> normal;
  auto *data = x.HostWrite();
  for (int i = 0; i < x.Size(); i++) data[i] = normal(generator);
}
void Fill(ComplexVector &x, unsigned int seed)
{
  Fill(x.Real(), seed); Fill(x.Imag(), seed+17);
}
template <class V> auto Alpha()
{
  if constexpr (std::is_same_v<V, Vector>) return -0.375;
  else return std::complex<double>(-0.375, 0.625);
}
template <class V> double Difference(const V &x, const V &y)
{
  V error(x); error.UseDevice(x.UseDevice()); error -= y;
  return linalg::Norml2(MPI_COMM_WORLD, error) /
         std::max(linalg::Norml2(MPI_COMM_WORLD, y), 1e-300);
}

template <class V> json Arithmetic(int n, bool gpu)
{
  V original(n), full(n), unpacked(n), partial;
  original.UseDevice(gpu); full.UseDevice(gpu); unpacked.UseDevice(gpu);
  Fill(original, 41+n); Fill(full, 53+n);
  if constexpr (std::is_same_v<V, ComplexVector>)
  {
    if (n == 1)
    {
      original.Real().HostWrite()[0] = 2.; original.Imag().HostWrite()[0] = 3.;
      full.Real().HostWrite()[0] = 5.; full.Imag().HostWrite()[0] = 7.;
    }
  }
  StoredBasisVector packed; packed.Pack(original); packed.Unpack(unpacked);
  // The stored vector must own its float data, independently of its source.
  original = 0.0;
  using Scalar = decltype(linalg::Dot(MPI_COMM_WORLD, full, unpacked));
  const Scalar reference = n ? linalg::Dot(MPI_COMM_WORLD, full, unpacked) : Scalar{};
  const Scalar direct = packed.Dot(MPI_COMM_WORLD, full, partial);
  const double scale = n ? std::max(linalg::Norml2(MPI_COMM_WORLD, full) *
      linalg::Norml2(MPI_COMM_WORLD, unpacked), 1e-300) : 1.;
  const double norm_error = std::abs(direct-reference)/scale;
  const double relative = std::abs(direct-reference)/std::max(std::abs(reference), 1e-300);
  V legacy(full), candidate(full); legacy.UseDevice(gpu); candidate.UseDevice(gpu);
  if (n) legacy.Add(Alpha<V>(), unpacked);
  packed.AddTo(Alpha<V>(), candidate);
  const double axpy = n ? Difference(candidate, legacy) : 0.;
  bool detector = true;
  if constexpr (std::is_same_v<V, ComplexVector>)
  {
    if (n == 1)
    {
      // Incorrect conjugation would yield 31+i instead of 31-i and must fail.
      detector = std::abs(direct-std::complex<double>(31., -1.)) < 1e-12 &&
                 std::abs(direct-std::complex<double>(31., 1.))/scale > 1e-3;
    }
  }
  return json{{"n",n},{"real",std::is_same_v<V,Vector>},{"dot_norm_scaled_error",norm_error},
    {"dot_relative_error",relative},{"axpy_relative_error",axpy},{"scratch_size",partial.Size()},
    {"source_overwrite_test",true},{"conjugation_fault_detected",detector},
    {"passed",norm_error<1e-12 && relative<1e-12 && axpy<1e-12 && detector && partial.Size()<=65536}};
}

template <class V> json Orthogonality(bool gpu)
{
  constexpr int n = 4097, count = 16;
  std::vector<StoredBasisVector> basis(count);
  V q(n), unpacked(n), partial;
  q.UseDevice(gpu); unpacked.UseDevice(gpu);
  for (int j = 0; j < count; j++)
  {
    Fill(q, 501+j);
    for (int k = 0; k < j; k++)
    {
      basis[k].Unpack(unpacked);
      q.Add(-linalg::Dot(MPI_COMM_WORLD, q, unpacked), unpacked);
    }
    q *= 1./linalg::Norml2(MPI_COMM_WORLD, q);
    basis[j].Pack(q);
  }
  V left(n), right(n); left.UseDevice(gpu); right.UseDevice(gpu);
  double gram_error = 0.;
  for (int j = 0; j < count; j++)
  {
    basis[j].Unpack(left);
    for (int k = 0; k <= j; k++)
    {
      basis[k].Unpack(right);
      gram_error = std::max(gram_error,
        std::abs(linalg::Dot(MPI_COMM_WORLD,left,right)-double(j==k)));
    }
  }
  Fill(q, 902);
  V legacy(q), candidate(q); legacy.UseDevice(gpu); candidate.UseDevice(gpu);
  double coefficient_delta = 0.;
  for (int k = 0; k < count; k++)
  {
    basis[k].Unpack(unpacked);
    const auto old = linalg::Dot(MPI_COMM_WORLD,legacy,unpacked);
    const auto direct = basis[k].Dot(MPI_COMM_WORLD,candidate,partial);
    coefficient_delta = std::max(coefficient_delta,std::abs(old-direct));
    legacy.Add(-old,unpacked); basis[k].AddTo(-direct,candidate);
  }
  legacy *= 1./linalg::Norml2(MPI_COMM_WORLD,legacy);
  candidate *= 1./linalg::Norml2(MPI_COMM_WORLD,candidate);
  double old_orth = 0., direct_orth = 0.;
  for (int k = 0; k < count; k++)
  {
    basis[k].Unpack(unpacked);
    old_orth = std::max(old_orth,std::abs(linalg::Dot(MPI_COMM_WORLD,legacy,unpacked)));
    direct_orth = std::max(direct_orth,std::abs(linalg::Dot(MPI_COMM_WORLD,candidate,unpacked)));
  }
  const double difference = Difference(candidate,legacy);
  return json{{"real",std::is_same_v<V,Vector>},{"n",n},{"basis_vectors",count},
    {"packed_gram_max_error",gram_error},{"legacy_orth_max",old_orth},{"direct_orth_max",direct_orth},
    {"coefficient_max_abs_delta",coefficient_delta},{"normalized_vector_delta",difference},
    {"passed",gram_error<2e-7 && old_orth<2e-7 && direct_orth<2e-7 && difference<1e-12}};
}
}

int main(int argc, char **argv)
{
  if (argc!=3 || (std::string(argv[1])!="cpu" && std::string(argv[1])!="cuda")) return 1;
  const auto begin = std::chrono::steady_clock::now();
  const bool gpu = std::string(argv[1])=="cuda";
  Mpi::Init(argc,argv);
  MFEM_VERIFY(Mpi::Size(MPI_COMM_WORLD)==1,"Probe requires one MPI rank");
  mfem::Device device(gpu ? "cuda" : "cpu");
  hypre::Initialize();
  std::size_t pool = 0;
#if defined(HYPRE_USING_UMPIRE)
  if (gpu)
  {
    pool = 256*1024*1024;
    MFEM_VERIFY(HYPRE_SetUmpireDevicePoolSize(pool)==0,"Cannot configure bounded HYPRE pool");
  }
#endif
  json rows = json::array();
  for (int n : {0,1,1009,65537,131071})
  {
    rows.push_back(Arithmetic<Vector>(n,gpu));
    rows.push_back(Arithmetic<ComplexVector>(n,gpu));
  }
  json mgs = {Orthogonality<Vector>(gpu),Orthogonality<ComplexVector>(gpu)};
  bool passed = true;
  for (const auto &row : rows) passed = passed && row.at("passed").get<bool>();
  for (const auto &row : mgs) passed = passed && row.at("passed").get<bool>();
  struct rusage usage{}; getrusage(RUSAGE_SELF,&usage);
  json report{{"scope","Actual Palace StoredBasisVector methods, one-rank arithmetic/MGS control"},
    {"device",gpu?"cuda":"cpu"},{"execution_passed",true},{"arithmetic_passed",passed},
    {"storage","FP32"},{"arithmetic","FP64"},{"accumulation","FP64"},{"tensor_cores",false},
    {"hypre_initial_device_pool_bytes",pool},{"mfem_memory_type",int(mfem::Device::GetMemoryType())},
    {"rows",rows},{"mgs",mgs},{"target",{{"same_storage",1e-12},{"gram_and_orth",2e-7}}},
    {"elapsed_seconds",std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()},
    {"max_rss_bytes",usage.ru_maxrss*1024},
    {"limitations",{"Single rank, not distributed ownership or multi-GPU", "Well-conditioned deterministic MGS; no nearly dependent basis guarantee", "No operator solve, antenna or performance qualification"}}};
  std::ofstream output(argv[2]); output << report.dump(2) << '\n'; output.close();
  if (!output) return 3;
  std::cout << "STORED_BASIS_PROBE: device=" << argv[1] << " passed=" << passed << '\n';
  return passed ? 0 : 2;
}
