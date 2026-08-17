#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
mkdir -p "${DIST_DIR}"

tar -czf "${DIST_DIR}/financial-data-platform-bundle.tgz" \
  --exclude=".git" \
  --exclude=".venv" \
  --exclude="dist" \
  --exclude="data/generated" \
  --exclude="__pycache__" \
  -C "${ROOT_DIR}" \
  .

echo "Created ${DIST_DIR}/financial-data-platform-bundle.tgz"

