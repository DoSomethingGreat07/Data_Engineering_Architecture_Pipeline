#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

docker compose run --rm dbt dbt deps --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial
docker compose run --rm dbt dbt compile --project-dir /workspace/dbt_financial --profiles-dir /workspace/dbt_financial

