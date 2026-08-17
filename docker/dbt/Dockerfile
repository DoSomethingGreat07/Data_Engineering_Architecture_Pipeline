FROM python:3.11-slim

RUN pip install --no-cache-dir "dbt-athena-community~=1.8.0"

WORKDIR /workspace
COPY dbt_financial /workspace/dbt_financial
