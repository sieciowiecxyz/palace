// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Native table parser/writer tests need MPI, but no MFEM Device, HYPRE, CEED or solve.
// Link test/unit/test-tablecsv.cpp and test/unit/fixtures.cpp against current headers.
#include <catch2/catch_session.hpp>
#include "utils/communication.hpp"

int main(int argc, char *argv[])
{
  palace::Mpi::Init(argc, argv);
  int result = 0;
  {
    Catch::Session session;
    result = session.applyCommandLine(argc, argv);
    if (!result)
    {
      result = session.run();
    }
  }
  palace::Mpi::Finalize();
  return result;
}
