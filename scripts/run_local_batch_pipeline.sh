#!/usr/bin/env bash
set -euo pipefail

PYSPARK_BIN_DIR="$(python - <<'PY'
import os
import pyspark

print(os.path.join(os.path.dirname(pyspark.__file__), "bin"))
PY
)"

unset SPARK_HOME
export PATH="${PYSPARK_BIN_DIR}:${PATH}"
export PYSPARK_PYTHON="$(command -v python)"

python -m databricks.batch.financial_batch_pipeline \
  --bronze-root data/lakehouse/batch/raw \
  --silver-root data/lakehouse/batch/silver \
  --gold-root data/lakehouse/batch/gold \
  --rejected-root data/lakehouse/batch/rejected \
  --disable-ge-validation
