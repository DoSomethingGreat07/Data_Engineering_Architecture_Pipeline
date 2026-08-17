from pathlib import Path

from src.batch_producer.discovery import discover_batch_files
from src.validation.batch_suite_map import SUITE_BY_DATASET


def test_extracted_batch_validation_inputs_are_discoverable() -> None:
    files = discover_batch_files("data/external_sources/canonical", latest_only=True)
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
