#!/usr/bin/env bash
#
# The gate for this repo: the GitHub workflow runs this script and nothing
# else, so a local pass is a CI pass. Run it before committing.
#
# The suite's integration tests start their own RabbitMQ and TimescaleDB
# through testcontainers and self-skip without docker.
#
# Usage: ./ci.sh
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

step() { printf '\n=== %s ===\n' "$1"; shift; "$@"; }

step "uv sync (locked)" uv sync --all-extras --all-groups --locked
step "ruff check" uv run ruff check --no-fix .
step "ruff format --check" uv run ruff format --check .
step "pyright" uv run pyright
step "sema snapshot staging check" uv run python -P \
  src/gjk/sema/check_staging.py src/gjk/sema_seed_request.yaml
step "tests" uv run pytest -q tests/

printf '\nAll checks passed.\n'
