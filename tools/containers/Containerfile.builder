# Layer over an exported, dependency-complete builder. The seed is recorded in tools/runtime.json.
# Deliberately preserves its compiled MFEM/libCEED/hypre and solver object files.
ARG SEED_IMAGE=localhost/palace:sm120-dev-seed-20261018
FROM ${SEED_IMAGE}
RUN apt-get update -qq && apt-get install -y --no-install-recommends ccache \
    && rm -rf /var/lib/apt/lists/*
