from __future__ import annotations

from datetime import datetime
from typing import Any

from common import default_args, streaming_task_specs

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except Exception:  # noqa: BLE001
    DAG = None
    PythonOperator = None


def noop_check(**context: Any) -> None:
    del context


def build_streaming_ops_dag():
    if DAG is None:
        return None

    with DAG(
        dag_id="financial_streaming_operations",
        start_date=datetime(2026, 8, 15),
        schedule="*/15 * * * *",
        catchup=False,
        default_args=default_args(),
        tags=["financial", "streaming", "operations"],
        description="Operational monitoring workflow for the financial streaming pipeline.",
    ) as dag:
        tasks: dict[str, Any] = {}
        for spec in streaming_task_specs():
            task = PythonOperator(task_id=spec.task_id, python_callable=noop_check)
            tasks[spec.task_id] = task

        for spec in streaming_task_specs():
            for downstream in spec.downstream_task_ids:
                tasks[spec.task_id] >> tasks[downstream]
        return dag


dag = build_streaming_ops_dag()
