import json
from pathlib import Path

from src.common.config import load_settings
from src.generators.synthetic_data import FinancialDataGenerator, write_datasets


def test_generation_is_deterministic() -> None:
    settings = load_settings("config/test.yaml")
    first_batch, first_stream, _ = FinancialDataGenerator(settings.generation).generate_all()
    second_batch, second_stream, _ = FinancialDataGenerator(settings.generation).generate_all()
    assert first_batch["customers"] == second_batch["customers"]
    assert first_batch["transactions"] == second_batch["transactions"]
    assert first_stream == second_stream


def test_generation_includes_required_anomalies() -> None:
    settings = load_settings("config/test.yaml")
    batch_datasets, stream_events, malformed_records = FinancialDataGenerator(
        settings.generation
    ).generate_all()

    transaction_ids = [row["transaction_id"] for row in batch_datasets["transactions"]]
    assert any(identifier is None for identifier in transaction_ids)
    assert len(set(filter(None, transaction_ids))) < len(list(filter(None, transaction_ids)))

    invalid_currency_rows = [
        row for row in batch_datasets["transactions"] if row["currency_code"] == "ZZZ"
    ]
    negative_amount_rows = [
        row for row in batch_datasets["transactions"] if float(row["transaction_amount"]) < 0
    ]
    assert invalid_currency_rows
    assert negative_amount_rows

    late_stream_events = [row for row in stream_events if row["late_arrival_flag"]]
    assert late_stream_events
    assert malformed_records


def test_write_datasets_creates_expected_files(tmp_path: Path) -> None:
    settings = load_settings("config/test.yaml")
    batch_datasets, stream_events, malformed_stream_events = FinancialDataGenerator(
        settings.generation
    ).generate_all()

    paths = write_datasets(
        tmp_path,
        batch_datasets,
        stream_events,
        malformed_stream_events,
    )

    assert paths.customers_csv.exists()
    assert paths.ingest_ready_dir.exists()
    assert paths.stream_events_jsonl.exists()
    assert (paths.ingest_ready_dir / "customers_20260815T120000Z.json").exists()

    customers = json.loads(paths.customers_json.read_text(encoding="utf-8"))
    stream_lines = paths.stream_events_jsonl.read_text(encoding="utf-8").strip().splitlines()

    assert len(customers) == settings.generation.customers
    assert len(stream_lines) >= settings.generation.stream_events
