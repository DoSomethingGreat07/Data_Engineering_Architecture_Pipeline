def test_bronze_batch_pipeline_uses_json_for_canonical_datasets() -> None:
    from databricks.common.source_formats import source_format_for_dataset

    assert source_format_for_dataset("customers") == "json"
    assert source_format_for_dataset("accounts") == "json"
    assert source_format_for_dataset("transactions") == "json"
    assert source_format_for_dataset("securities") == "json"
