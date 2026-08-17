#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3.11}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

"${PYTHON_BIN}" -m venv --clear .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/development.txt

echo "Bootstrap complete using ${PYTHON_BIN}. Activate with: source .venv/bin/activate"
