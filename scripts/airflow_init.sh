#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

docker compose run --rm airflow-webserver bash -lc \
  "airflow db migrate && \
   airflow users create --username admin --password admin --firstname Airflow --lastname Admin --role Admin --email admin@example.com || true"

echo "Airflow metadata database initialized."

