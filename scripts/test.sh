#!/usr/bin/env bash
# Copyright (c) 2026 The University of Texas at Austin
# SPDX-License-Identifier: BSD-3-Clause
#
# Run the CoreForge test suite on any platform.
#
# CoreForge needs OpenMC, and OpenMC is harder to install than it looks:
#
#   - it is not on PyPI at all
#   - conda-forge builds it for linux-64 only; there is no osx-arm64 build
#   - the openmc/openmc image is amd64-only, on every tag
#
# So on Apple Silicon there is no native path, and CI never surfaces the problem
# because CI is ubuntu. This script closes that gap: it runs pytest directly
# when OpenMC is importable, and falls back to the container when it is not.
# Same command either way.
#
#   scripts/test.sh                              # whole suite
#   scripts/test.sh test/unit/test_materials.py  # one file
#   scripts/test.sh -k thermal_scattering        # one expression
#
# Arguments are passed through to pytest.
#
# On Apple Silicon the container runs under x86 emulation and is several times
# slower than native. Target a file or a -k expression while iterating; leave
# the full run to CI.
#
# MPACTPy is expected beside this repo; override with MPACTPY_DIR=/path.
# The image can be pinned with OPENMC_IMAGE=openmc/openmc:v0.15.3.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MPACTPY_DIR="${MPACTPY_DIR:-$(cd "$REPO_ROOT/.." && pwd)/MPACTPy}"
IMAGE="${OPENMC_IMAGE:-openmc/openmc:latest}"

if python -c "import openmc" >/dev/null 2>&1; then
    echo "▶ openmc importable — running natively"
    exec python -m pytest "${@:-test/unit/}"
fi

if ! command -v docker >/dev/null 2>&1; then
    cat >&2 <<'MSG'
✗ Neither OpenMC nor Docker is available.

  OpenMC is not on PyPI, and conda-forge has no osx-arm64 build, so on Apple
  Silicon the container is the only option. Install Docker, or use a linux-64
  machine where `mamba install -c conda-forge openmc` works.
MSG
    exit 1
fi

if [ ! -d "$MPACTPY_DIR" ]; then
    cat >&2 <<MSG
✗ MPACTPy not found at ${MPACTPY_DIR}

  CoreForge imports mpactpy for its rounding and tolerance helpers. Clone it
  beside this repository, or set MPACTPY_DIR=/path/to/MPACTPy.
MSG
    exit 1
fi

echo "▶ openmc not importable — running in ${IMAGE}"

# Read-only mounts plus PYTHONPATH rather than an install: nothing is written to
# the working tree, so a container run cannot leave build artefacts behind or
# disturb an editable install. -p no:cacheprovider because pytest cannot write
# its cache onto a read-only mount.
exec docker run --rm \
    -v "$REPO_ROOT:/work/CoreForge:ro" \
    -v "$MPACTPY_DIR:/work/MPACTPy:ro" \
    -e PYTHONPATH=/work/CoreForge:/work/MPACTPy \
    -w /work/CoreForge \
    "$IMAGE" \
    python -m pytest -p no:cacheprovider "${@:-test/unit/}"
