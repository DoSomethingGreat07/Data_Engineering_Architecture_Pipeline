# Airflow

This directory contains the Phase 9 orchestration layer.

Local Docker environment:
- `make airflow-up`
- `make airflow-down`

Production-style DAGs:
- `airflow/dags/financial_batch_workflow.py`
- `airflow/dags/financial_streaming_operations.py`

Batch DAG coverage:
- Plaid sandbox batch extraction
- Great Expectations validation of extracted canonical files
- Bronze upload to S3
- Local Spark batch processing to Silver and Gold
- Publish Silver/Gold Delta outputs to S3
- dbt run and dbt test on Athena/Glue
- Reconciliation preview query
- QuickSight Athena handoff package generation from reporting marts
- Batch execution report generation in `reports/`

These DAGs are parameterized and do not embed credentials.
