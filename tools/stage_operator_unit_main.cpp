// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Small entry point for the existing test-spaceoperator.cpp cases. This deliberately
// omits the regression harness and any linear solve; build against current headers.
#include <cstdio>
#include <string>
#include <catch2/catch_session.hpp>
#include <mfem.hpp>
#include "fem/libceed/ceed.hpp"
#include "linalg/hypre.hpp"
#include "utils/communication.hpp"
#include "utils/device.hpp"
#include "utils/omp.hpp"

namespace
{
void Mark(const char *stage)
{
  std::fprintf(stderr, "PALACE_OPERATOR_INIT %s\n", stage);
  std::fflush(stderr);
}
}  // namespace

int main(int argc, char *argv[])
{
  using namespace palace;
  Mark("before_mpi_init");
  Mpi::Init(argc, argv);
  Mark("after_mpi_init");
  int result = 0;
  {
    Catch::Session session;
    std::string device_string = "cpu";
    std::string backend = "/cpu/self";
    std::string jit_source = "/opt/palace-cudss/include/palace/";
    using namespace Catch::Clara;
    session.cli(session.cli() |
                Opt(device_string, "device")["--device"]("MFEM device") |
                Opt(backend, "backend")["--backend"]("libCEED backend") |
                Opt(jit_source, "path")["--jit-source"]("Palace installed JIT source"));
    Mark("before_session_parse");
    result = session.applyCommandLine(argc, argv);
    Mark("after_session_parse");
    if (!result)
    {
      Mark("before_configure_omp");
      const int threads = utils::ConfigureOmp();
      Mark("after_configure_omp");
      const bool use_gpu = device_string == "cuda";
      const int device_id = use_gpu ? utils::GetDeviceId(Mpi::World(), utils::GetDeviceCount()) : 0;
      if (threads > 0)
      {
        device_string += ",omp";
      }
      Mark("before_device");
      mfem::Device device(device_string.c_str(), device_id);
      Mark("after_device");
      Mark("before_hypre_init");
      hypre::Initialize();
      Mark("after_hypre_init");
      Mark("before_ceed_init");
      ceed::Initialize(backend.c_str(), jit_source.c_str());
      Mark("after_ceed_init");
      Mark("before_session_run");
      result = session.run();
      Mark("after_session_run");
      Mark("before_ceed_finalize");
      ceed::Finalize();
      Mark("after_ceed_finalize");
    }
  }
  Mark("before_mpi_finalize");
  Mpi::Finalize();
  Mark("after_mpi_finalize");
  return result;
}
