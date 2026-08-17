from airflow.dags.common import batch_task_specs, streaming_task_specs


def test_batch_workflow_task_order() -> None:
    specs = {spec.task_id: spec for spec in batch_task_specs()}
    assert specs["extract_plaid_batch"].downstream_task_ids == ["validate_extracted_batch"]
    assert specs["validate_extracted_batch"].downstream_task_ids == ["upload_bronze_batch"]
    assert specs["run_dbt_models"].downstream_task_ids == ["run_dbt_tests"]
    assert specs["run_dbt_tests"].downstream_task_ids == ["run_reconciliation"]
    assert specs["run_reconciliation"].downstream_task_ids == ["prepare_quicksight_handoff"]
    assert specs["prepare_quicksight_handoff"].downstream_task_ids == ["generate_run_report"]
    assert specs["generate_run_report"].downstream_task_ids == ["publish_success_metrics"]
    assert specs["publish_success_metrics"].downstream_task_ids == []


def test_streaming_workflow_task_order() -> None:
    specs = {spec.task_id: spec for spec in streaming_task_specs()}
    assert specs["capture_alpaca_to_kinesis"].downstream_task_ids == ["consume_kinesis_microbatch"]
    assert specs["consume_kinesis_microbatch"].downstream_task_ids == ["validate_stream_microbatch"]
    assert specs["validate_stream_microbatch"].downstream_task_ids == ["run_stream_spark_transform"]
    assert specs["run_stream_spark_transform"].downstream_task_ids == ["publish_stream_curated"]
    assert specs["publish_stream_curated"].downstream_task_ids == ["register_stream_glue_catalog"]
    assert specs["register_stream_glue_catalog"].downstream_task_ids == ["run_stream_athena_smoke_test"]
    assert specs["run_stream_athena_smoke_test"].downstream_task_ids == ["run_stream_dbt_models"]
    assert specs["run_stream_dbt_models"].downstream_task_ids == ["run_stream_dbt_tests"]
    assert specs["run_stream_dbt_tests"].downstream_task_ids == ["prepare_stream_quicksight_handoff"]
    assert specs["prepare_stream_quicksight_handoff"].downstream_task_ids == ["publish_stream_success_metrics"]
    assert specs["publish_stream_success_metrics"].downstream_task_ids == []
