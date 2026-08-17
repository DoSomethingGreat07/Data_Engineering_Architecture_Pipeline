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

python -m databricks.streaming.financial_streaming_microbatch_pipeline \
  --raw-root data/lakehouse/streaming/raw \
  --silver-root data/lakehouse/streaming/silver \
  --gold-root data/lakehouse/streaming/gold \
  --rejected-root data/lakehouse/streaming/rejected
