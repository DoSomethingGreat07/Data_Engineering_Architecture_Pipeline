FROM apache/airflow:2.10.0-python3.11

ENV PATH="/home/airflow/.local/bin:${PATH}"

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements /tmp/requirements
ARG AIRFLOW_CONSTRAINTS_URL="https://raw.githubusercontent.com/apache/airflow/constraints-2.10.0/constraints-3.11.txt"
RUN pip install --no-cache-dir \
    --constraint "${AIRFLOW_CONSTRAINTS_URL}" \
    -r /tmp/requirements/airflow.txt
RUN pip install --no-cache-dir -r /tmp/requirements/airflow-runtime.txt
RUN pip install --no-cache-dir \
    --constraint "${AIRFLOW_CONSTRAINTS_URL}" \
    "dbt-athena-community~=1.8.0"
