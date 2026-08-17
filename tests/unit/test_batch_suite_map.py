from src.validation.batch_suite_map import SUITE_BY_DATASET


def test_batch_suite_map_covers_core_extracted_datasets() -> None:
    assert SUITE_BY_DATASET["customers"] == "customers_bronze"
    assert SUITE_BY_DATASET["accounts"] == "accounts_bronze"
    assert SUITE_BY_DATASET["transactions"] == "transactions_bronze"
    assert SUITE_BY_DATASET["securities"] == "securities_bronze"
