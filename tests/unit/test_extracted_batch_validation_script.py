import json
from pathlib import Path

from src.batch_producer.discovery import discover_batch_files
from src.validation.batch_suite_map import SUITE_BY_DATASET


def test_extracted_batch_validation_inputs_are_discoverable(tmp_path: Path) -> None:
    canonical_root = tmp_path / "canonical"
    canonical_root.mkdir()

    (canonical_root / "accounts_20260817T000001Z.json").write_text(
        json.dumps([{"account_id": "ACC-1"}]),
        encoding="utf-8",
    )
    (canonical_root / "customers_20260817T000001Z.json").write_text(
        json.dumps([{"customer_id": "CUST-1"}]),
        encoding="utf-8",
    )
    (canonical_root / "transactions_20260817T000001Z.json").write_text(
        json.dumps([{"transaction_id": "TXN-1"}]),
        encoding="utf-8",
    )

    files = discover_batch_files(canonical_root, latest_only=True)
    discovered_datasets = {path.name.split("_", 1)[0] for path in files}
    assert "accounts" in discovered_datasets
    assert "customers" in discovered_datasets
    assert "transactions" in discovered_datasets


def test_customer_and_account_expectation_specs_exist() -> None:
    for suite_name in (
        SUITE_BY_DATASET["customers"],
        SUITE_BY_DATASET["accounts"],
        SUITE_BY_DATASET["transactions"],
    ):
        path = Path("great_expectations/expectations") / f"{suite_name}.json"
        assert path.exists()
