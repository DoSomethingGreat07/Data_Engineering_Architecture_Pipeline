from pathlib import Path

import pandas as pd

from src.validation.gx_runner import (
    bootstrap_context_directory,
    load_suite_spec,
    validate_pandas_dataframe,
)


def test_load_suite_spec_reads_repo_expectation_definition() -> None:
    spec = load_suite_spec("great_expectations", "transactions_bronze")
    assert spec.suite_name == "transactions_bronze"
    assert spec.expectations


def test_bootstrap_context_directory_creates_context_root(tmp_path: Path) -> None:
    ge_root = tmp_path / "great_expectations"
    bootstrap_context_directory(ge_root)
    assert ge_root.exists()


def test_validate_pandas_dataframe_writes_summary_files(tmp_path: Path) -> None:
    ge_root = tmp_path / "great_expectations"
    expectations_dir = ge_root / "expectations"
    expectations_dir.mkdir(parents=True)
    spec_path = expectations_dir / "transactions_bronze.json"
    source_spec = Path("great_expectations/expectations/transactions_bronze.json")
    spec_path.write_text(source_spec.read_text(encoding="utf-8"), encoding="utf-8")

    dataframe = pd.DataFrame(
        [
            {
                "transaction_id": "TXN-1",
                "account_id": "ACCT-1",
                "customer_id": "CUST-1",
                "transaction_type": "DEBIT",
                "transaction_amount": 100.0,
                "currency_code": "USD",
                "transaction_status": "POSTED",
                "event_timestamp": "2026-08-15T12:00:00Z",
                "processing_timestamp": "2026-08-15T12:05:00Z",
                "merchant_category": "GROCERY",
                "country_code": "US",
                "risk_score": 10,
            }
        ]
    )

    summary = validate_pandas_dataframe(
        ge_root=ge_root,
        suite_name="transactions_bronze",
        dataframe=dataframe,
        datasource_name="test_datasource",
        asset_name="test_asset",
        batch_definition_name="whole_dataframe",
        stage="bronze_post_ingest",
        dataset_name="transactions",
        result_output_dir=ge_root / "results",
    )

    assert summary.success is True
    result_path = Path(summary.result_path)
    assert result_path.exists()
    metric_path = result_path.with_name(result_path.stem + "_cloudwatch_metric.json")
    assert metric_path.exists()
