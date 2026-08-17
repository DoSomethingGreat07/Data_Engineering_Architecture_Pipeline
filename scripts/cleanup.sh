#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

rm -rf data/generated data/generated-test
rm -rf dist
docker compose down --volumes --remove-orphans || true

echo "Local generated data and Docker resources cleaned up."
echo "Phase 2+ cloud cleanup commands will be added before any terraform apply guidance."
