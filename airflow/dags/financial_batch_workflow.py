from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from common import batch_task_specs, default_args

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    from airflow.operators.python import PythonOperator
except Exception:  # noqa: BLE001
    DAG = None
    BashOperator = PythonOperator = None


def emit_metric(**context: Any) -> None:
    del context


def _batch_env() -> dict[str, str]:
    return {
        "AWS_REGION": os.environ.get("AWS_REGION", "us-east-1"),
        "AWS_PROFILE": os.environ.get("AWS_PROFILE", "default"),
        "ATHENA_CATALOG": os.environ.get("ATHENA_CATALOG", "awsdatacatalog"),
        "ATHENA_WORKGROUP": os.environ.get("ATHENA_WORKGROUP", "primary"),
        "ATHENA_STAGING_DIR": os.environ.get(
            "ATHENA_STAGING_DIR",
            "s3://fdp-batch-only-change-me/athena/results/",
        ),
        "ATHENA_TARGET_SCHEMA": os.environ.get(
            "ATHENA_TARGET_SCHEMA",
            "fdp_dev_batch_analytics",
        ),
        "S3_DATA_LAKE_BUCKET": os.environ.get(
            "S3_DATA_LAKE_BUCKET",
            "fdp-batch-only-change-me",
        ),
        "PLAID_BATCH_CUSTOMER_ID": os.environ.get(
            "PLAID_BATCH_CUSTOMER_ID",
            "CUST-NFCU-001",
        ),
        "PLAID_BATCH_FULL_NAME": os.environ.get(
            "PLAID_BATCH_FULL_NAME",
            "Navy Federal Member",
        ),
        "PLAID_BATCH_EMAIL": os.environ.get(
            "PLAID_BATCH_EMAIL",
            "member@example.com",
        ),
        "PLAID_BATCH_CUSTOMER_COUNT": os.environ.get(
            "PLAID_BATCH_CUSTOMER_COUNT",
            "20",
        ),
    }


def _batch_bash_command(task_id: str) -> str:
    commands = {
        "extract_plaid_batch": (
            "python -m src.sources.plaid_batch.cli "
            '--customer-id "$PLAID_BATCH_CUSTOMER_ID" '
            '--full-name "$PLAID_BATCH_FULL_NAME" '
            '--email "$PLAID_BATCH_EMAIL" '
            '--customer-count "$PLAID_BATCH_CUSTOMER_COUNT" '
            '--scenario-seed "$AIRFLOW_CTX_DAG_RUN_ID" '
            "--run-sandbox-seeded-extract --print-record-limit 2"
        ),
        "validate_extracted_batch": (
            "python great_expectations/scripts/run_extracted_batch_validations.py "
            "--input-dir data/external_sources/canonical --latest-only"
        ),
        "upload_bronze_batch": (
            "python -m src.batch_producer.cli "
            '--bucket "$S3_DATA_LAKE_BUCKET" '
            "--input-dir data/external_sources/canonical --latest-only "
            '--aws-region "$AWS_REGION" --aws-profile "$AWS_PROFILE"'
        ),
        "stage_local_bronze": (
            "python -m src.batch_preparation.cli "
            "--canonical-root data/external_sources/canonical "
            "--bronze-root data/lakehouse/batch/raw"
        ),
        "run_spark_batch": "bash /workspace/scripts/run_local_batch_pipeline.sh ",
        "publish_curated_batch": (
            "python -m src.batch_publisher.cli "
            '--bucket "$S3_DATA_LAKE_BUCKET" '
            '--aws-region "$AWS_REGION" --aws-profile "$AWS_PROFILE"'
        ),
        "run_dbt_models": (
            "/home/airflow/.local/bin/dbt run --project-dir /workspace/dbt_financial "
            "--profiles-dir /workspace/dbt_financial"
        ),
        "run_dbt_tests": (
            "/home/airflow/.local/bin/dbt test --project-dir /workspace/dbt_financial "
            "--profiles-dir /workspace/dbt_financial"
        ),
        "run_reconciliation": (
            "/home/airflow/.local/bin/dbt show --project-dir /workspace/dbt_financial "
            "--profiles-dir /workspace/dbt_financial "
            '--inline "select * from '
            '\\"awsdatacatalog\\".\\"fdp_dev_batch_analytics_marts\\".'
            '\\"mart_regulatory_reconciliation\\""'
        ),
        "prepare_quicksight_handoff": (
            "python -m src.quicksight_handoff.cli "
            "--output-dir quicksight/output "
            '--catalog "$ATHENA_CATALOG" '
            '--schema "$ATHENA_TARGET_SCHEMA" '
            '--workgroup "$ATHENA_WORKGROUP" '
            '--staging-dir "$ATHENA_STAGING_DIR" '
            '--aws-region "$AWS_REGION" '
            '--aws-profile "$AWS_PROFILE" '
            '--quicksight-region "$AWS_REGION"'
        ),
        "generate_run_report": (
            "python -m src.run_report.cli "
            "--output-dir reports "
            '--run-id "$AIRFLOW_CTX_DAG_RUN_ID" '
            '--execution-date "$AIRFLOW_CTX_EXECUTION_DATE" '
            '--bucket "$S3_DATA_LAKE_BUCKET" '
            '--aws-region "$AWS_REGION" '
            '--aws-profile "$AWS_PROFILE"'
        ),
    }
    return commands[task_id]


def build_batch_dag():
    if DAG is None:
        return None

    with DAG(
        dag_id="financial_batch_workflow",
        start_date=datetime(2026, 8, 15),
        schedule="0 2 * * *",
        catchup=False,
        default_args=default_args(),
        tags=["financial", "batch", "production"],
        description="Batch workflow for the financial data platform.",
    ) as dag:
        tasks: dict[str, Any] = {}
        for spec in batch_task_specs():
            if spec.operator == "BashOperator":
                task = BashOperator(
                    task_id=spec.task_id,
                    bash_command=_batch_bash_command(spec.task_id),
                    cwd="/workspace",
                    env=_batch_env(),
                )
            else:
                task = PythonOperator(
                    task_id=spec.task_id,
                    python_callable=emit_metric,
                )
            tasks[spec.task_id] = task

        for spec in batch_task_specs():
            for downstream in spec.downstream_task_ids:
                tasks[spec.task_id] >> tasks[downstream]
        return dag


dag = build_batch_dag()
