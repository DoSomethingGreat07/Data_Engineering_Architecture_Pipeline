from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from common import default_args, streaming_task_specs

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator
    from airflow.operators.python import PythonOperator
except Exception:  # noqa: BLE001
    DAG = None
    BashOperator = PythonOperator = None


def emit_metric(**context: Any) -> None:
    del context


def _stream_env() -> dict[str, str]:
    streaming_bucket = os.environ.get(
        "STREAMING_S3_BUCKET",
        os.environ.get("S3_DATA_LAKE_BUCKET", "fdp-batch-only-change-me"),
    )
    return {
        "AWS_REGION": os.environ.get("AWS_REGION", "us-east-1"),
        "AWS_PROFILE": os.environ.get("AWS_PROFILE", "default"),
        "STREAMING_S3_BUCKET": streaming_bucket,
        "KINESIS_STREAM_NAME": os.environ.get("KINESIS_STREAM_NAME", "fdp-dev-events"),
        "STREAMING_GLUE_DATABASE": os.environ.get(
            "STREAMING_GLUE_DATABASE",
            "fdp_dev_streaming_lakehouse",
        ),
        "STREAMING_ATHENA_WORKGROUP": os.environ.get("STREAMING_ATHENA_WORKGROUP", "primary"),
        "STREAMING_ATHENA_STAGING_DIR": os.environ.get(
            "STREAMING_ATHENA_STAGING_DIR",
            f"s3://{streaming_bucket}/athena/results/",
        ),
        "STREAMING_ATHENA_DBT_DATA_DIR": os.environ.get(
            "STREAMING_ATHENA_DBT_DATA_DIR",
            f"s3://{streaming_bucket}/dbt/",
        ),
        "STREAMING_ATHENA_TARGET_SCHEMA": os.environ.get(
            "STREAMING_ATHENA_TARGET_SCHEMA",
            "fdp_dev_streaming_analytics",
        ),
        "ATHENA_CATALOG": os.environ.get("ATHENA_CATALOG", "awsdatacatalog"),
        "DBT_TARGET": "streaming",
        "ALPACA_API_KEY_ID": os.environ.get("ALPACA_API_KEY_ID", ""),
        "ALPACA_API_SECRET_KEY": os.environ.get("ALPACA_API_SECRET_KEY", ""),
        "ALPACA_STREAM_BASE_URL": os.environ.get(
            "ALPACA_STREAM_BASE_URL",
            "wss://stream.data.alpaca.markets",
        ),
        "ALPACA_STREAM_DATA_VERSION": os.environ.get(
            "ALPACA_STREAM_DATA_VERSION",
            "v2",
        ),
        "ALPACA_STREAM_FEED": os.environ.get("ALPACA_STREAM_FEED", "iex"),
        "ALPACA_STREAM_USE_TEST": os.environ.get("ALPACA_STREAM_USE_TEST", "false"),
        "ALPACA_STREAM_SYMBOLS": os.environ.get("ALPACA_STREAM_SYMBOLS", "AAPL,MSFT,SPY,QQQ"),
        "ALPACA_STREAM_MAX_MESSAGES": os.environ.get("ALPACA_STREAM_MAX_MESSAGES", "250"),
        "ALPACA_BROKER_ACCOUNT_ID": os.environ.get(
            "ALPACA_BROKER_ACCOUNT_ID",
            "ACCT-STREAM-001",
        ),
        "ALPACA_BROKER_CUSTOMER_ID": os.environ.get(
            "ALPACA_BROKER_CUSTOMER_ID",
            "CUST-STREAM-001",
        ),
    }


def _stream_bash_command(task_id: str) -> str:
    commands = {
        "capture_alpaca_to_kinesis": (
            "python -m src.sources.alpaca_streaming.cli "
            '--symbols "$ALPACA_STREAM_SYMBOLS" '
            '--max-messages "$ALPACA_STREAM_MAX_MESSAGES" '
            '--account-id "$ALPACA_BROKER_ACCOUNT_ID" '
            '--customer-id "$ALPACA_BROKER_CUSTOMER_ID" '
            '--kinesis-stream-name "$KINESIS_STREAM_NAME" '
            '--aws-region "$AWS_REGION" --aws-profile "$AWS_PROFILE"'
        ),
        "consume_kinesis_microbatch": (
            "python -m src.stream_consumer.cli "
            '--stream-name "$KINESIS_STREAM_NAME" '
            '--aws-region "$AWS_REGION" --aws-profile "$AWS_PROFILE" '
            "--output-dir data/external_sources/streaming "
            "--bronze-root data/lakehouse/streaming/raw --max-records 250"
        ),
        "validate_stream_microbatch": (
            "python great_expectations/scripts/run_stream_validation.py "
            "--input-dir data/external_sources/streaming/canonical/kinesis"
        ),
        "run_stream_spark_transform": "bash /workspace/scripts/run_local_streaming_pipeline.sh ",
        "publish_stream_curated": (
            "python -m src.stream_publisher.cli "
            '--bucket "$STREAMING_S3_BUCKET" '
            '--aws-region "$AWS_REGION" --aws-profile "$AWS_PROFILE"'
        ),
        "register_stream_glue_catalog": (
            "python -m src.stream_catalog.cli "
            '--bucket "$STREAMING_S3_BUCKET" '
            '--database-name "$STREAMING_GLUE_DATABASE" '
            '--aws-region "$AWS_REGION" --aws-profile "$AWS_PROFILE"'
        ),
        "run_stream_athena_smoke_test": (
            "python -m src.stream_athena.cli "
            '--database-name "$STREAMING_GLUE_DATABASE" '
            '--aws-region "$AWS_REGION" --aws-profile "$AWS_PROFILE" '
            '--workgroup "$STREAMING_ATHENA_WORKGROUP" '
            '--staging-dir "$STREAMING_ATHENA_STAGING_DIR"'
        ),
        "run_stream_dbt_models": (
            "/home/airflow/.local/bin/dbt run --project-dir /workspace/dbt_financial "
            "--profiles-dir /workspace/dbt_financial --select tag:streaming"
        ),
        "run_stream_dbt_tests": (
            "/home/airflow/.local/bin/dbt test --project-dir /workspace/dbt_financial "
            "--profiles-dir /workspace/dbt_financial --select tag:streaming"
        ),
        "prepare_stream_quicksight_handoff": (
            "python -m src.quicksight_handoff.cli "
            "--mode streaming "
            "--output-dir quicksight/streaming_output "
            '--catalog "$ATHENA_CATALOG" '
            '--schema "$STREAMING_ATHENA_TARGET_SCHEMA" '
            '--workgroup "$STREAMING_ATHENA_WORKGROUP" '
            '--staging-dir "$STREAMING_ATHENA_STAGING_DIR" '
            '--aws-region "$AWS_REGION" '
            '--aws-profile "$AWS_PROFILE" '
            '--quicksight-region "$AWS_REGION"'
        ),
    }
    return commands[task_id]


def build_streaming_dag():
    if DAG is None:
        return None

    with DAG(
        dag_id="financial_streaming_pipeline",
        start_date=datetime(2026, 8, 17),
        schedule="*/5 * * * *",
        catchup=False,
        default_args=default_args(),
        tags=["financial", "streaming", "realtime"],
        description="Realtime streaming workflow isolated from the batch financial pipeline.",
    ) as dag:
        tasks: dict[str, Any] = {}
        for spec in streaming_task_specs():
            if spec.operator == "BashOperator":
                task = BashOperator(
                    task_id=spec.task_id,
                    bash_command=_stream_bash_command(spec.task_id),
                    cwd="/workspace",
                    env=_stream_env(),
                )
            else:
                task = PythonOperator(task_id=spec.task_id, python_callable=emit_metric)
            tasks[spec.task_id] = task

        for spec in streaming_task_specs():
            for downstream in spec.downstream_task_ids:
                tasks[spec.task_id] >> tasks[downstream]
        return dag


dag = build_streaming_dag()
