#!/usr/bin/env bash
#
# Regenerate the vendored Sema snapshot under src/gjk/sema from the canonical
# sema repo.
#
# src/gjk/sema is GENERATED — never hand-edit it. To change what the snapshot
# contains, edit the seed (src/gjk/sema_seed_request.yaml) or the sema
# definitions, then re-run this script.
#
# This script owns only the gjk-specific wiring; the build mechanics are the
# sema CLI's (`sema snapshot --help` is the source of truth). The three glue
# facts a generic CLI can't know:
#   1. the seed lives at src/gjk/sema_seed_request.yaml
#   2. --package-name is `gjk`   (build derives import_root = <name>.sema =
#      gjk.sema; do NOT pass "gjk.sema")
#   3. the built tree is mirrored from <sema>/output/sema into src/gjk/sema
#
# The snapshot reflects the sema repo's CURRENT checkout — check out the sema
# ref you intend to ship from before running.
#
# Usage:
#   scripts/regen_sema_snapshot.sh                 # sibling ../sema checkout
#   SEMA_REPO=/path/to/sema scripts/regen_sema_snapshot.sh
set -euo pipefail

GJK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEMA_REPO="${SEMA_REPO:-$(cd "${GJK_ROOT}/../sema" 2>/dev/null && pwd || true)}"

if [[ -z "${SEMA_REPO}" || ! -d "${SEMA_REPO}" ]]; then
  echo "error: sema repo not found." >&2
  echo "       set SEMA_REPO=/path/to/sema and re-run (default looked for a" >&2
  echo "       sibling checkout at ${GJK_ROOT}/../sema)." >&2
  exit 1
fi

SEED="${GJK_ROOT}/src/gjk/sema_seed_request.yaml"
PACKAGE_NAME="gjk"

echo "==> sema repo: ${SEMA_REPO}"
echo "==> seed:      ${SEED}"
echo "==> package:   ${PACKAGE_NAME}"

cd "${SEMA_REPO}"
echo "==> sema snapshot prepare"
uv run sema snapshot prepare "${SEED}"
echo "==> sema snapshot build --package-name ${PACKAGE_NAME}"
uv run sema snapshot build --package-name "${PACKAGE_NAME}"

echo "==> mirror ${SEMA_REPO}/output/sema -> ${GJK_ROOT}/src/gjk/sema"
rsync -a --delete --exclude='__pycache__' \
  "${SEMA_REPO}/output/sema/" "${GJK_ROOT}/src/gjk/sema/"

echo "==> done. review the diff (git status) and run: uv run pytest -q"
