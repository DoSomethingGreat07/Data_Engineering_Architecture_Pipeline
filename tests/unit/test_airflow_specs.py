from airflow.dags.common import batch_task_specs, streaming_task_specs


def test_batch_task_count() -> None:
    assert len(batch_task_specs()) == 12


def test_streaming_task_count() -> None:
    assert len(streaming_task_specs()) == 11
