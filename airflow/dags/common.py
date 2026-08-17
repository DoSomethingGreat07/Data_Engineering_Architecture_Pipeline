from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any


@dataclass
class TaskSpec:
    task_id: str
    operator: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    downstream_task_ids: list[str] = field(default_factory=list)


def default_args() -> dict[str, Any]:
    return {
        "owner": "data-platform",
        "depends_on_past": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "execution_timeout": timedelta(minutes=30),
    }


def batch_task_specs() -> list[TaskSpec]:
    return [
        TaskSpec(
            "extract_plaid_batch",
            "BashOperator",
            downstream_task_ids=["validate_extracted_batch"],
        ),
        TaskSpec(
            "validate_extracted_batch",
            "BashOperator",
            downstream_task_ids=["upload_bronze_batch"],
        ),
        TaskSpec(
            "upload_bronze_batch",
            "BashOperator",
            downstream_task_ids=["stage_local_bronze"],
        ),
        TaskSpec(
            "stage_local_bronze",
            "BashOperator",
            downstream_task_ids=["run_spark_batch"],
        ),
        TaskSpec(
            "run_spark_batch",
            "BashOperator",
            downstream_task_ids=["publish_curated_batch"],
        ),
        TaskSpec(
            "publish_curated_batch",
            "BashOperator",
            downstream_task_ids=["run_dbt_models"],
        ),
        TaskSpec("run_dbt_models", "BashOperator", downstream_task_ids=["run_dbt_tests"]),
        TaskSpec(
            "run_dbt_tests",
            "BashOperator",
            downstream_task_ids=["run_reconciliation"],
        ),
        TaskSpec(
            "run_reconciliation",
            "BashOperator",
            downstream_task_ids=["prepare_quicksight_handoff"],
        ),
        TaskSpec(
            "prepare_quicksight_handoff",
            "BashOperator",
            downstream_task_ids=["generate_run_report"],
        ),
        TaskSpec(
            "generate_run_report",
            "BashOperator",
            downstream_task_ids=["publish_success_metrics"],
        ),
        TaskSpec("publish_success_metrics", "PythonOperator"),
    ]


def streaming_task_specs() -> list[TaskSpec]:
    return [
        TaskSpec(
            "capture_alpaca_to_kinesis",
            "BashOperator",
            downstream_task_ids=["consume_kinesis_microbatch"],
        ),
        TaskSpec(
            "consume_kinesis_microbatch",
            "BashOperator",
            downstream_task_ids=["validate_stream_microbatch"],
        ),
        TaskSpec(
            "validate_stream_microbatch",
            "BashOperator",
            downstream_task_ids=["run_stream_spark_transform"],
        ),
        TaskSpec(
            "run_stream_spark_transform",
            "BashOperator",
            downstream_task_ids=["publish_stream_curated"],
        ),
        TaskSpec(
            "publish_stream_curated",
            "BashOperator",
            downstream_task_ids=["register_stream_glue_catalog"],
        ),
        TaskSpec(
            "register_stream_glue_catalog",
            "BashOperator",
            downstream_task_ids=["run_stream_athena_smoke_test"],
        ),
        TaskSpec(
            "run_stream_athena_smoke_test",
            "BashOperator",
            downstream_task_ids=["run_stream_dbt_models"],
        ),
        TaskSpec(
            "run_stream_dbt_models",
            "BashOperator",
            downstream_task_ids=["run_stream_dbt_tests"],
        ),
        TaskSpec(
            "run_stream_dbt_tests",
            "BashOperator",
            downstream_task_ids=["prepare_stream_quicksight_handoff"],
        ),
        TaskSpec(
            "prepare_stream_quicksight_handoff",
            "BashOperator",
            downstream_task_ids=["publish_stream_success_metrics"],
        ),
        TaskSpec("publish_stream_success_metrics", "PythonOperator"),
    ]
