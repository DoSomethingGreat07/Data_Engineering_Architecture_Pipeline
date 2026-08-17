import json
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from src.batch_producer.service import BatchIngestionService
from src.batch_producer.validation import (
    compute_file_checksum,
    load_records,
    validate_batch_filename,
    validate_required_structure,
)
from src.common.storage import S3DataLakePaths


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: list[dict[str, object]] = []

    def put_object(self, **kwargs: object) -> dict[str, object]:
        self.objects.append(kwargs)
        return {"ETag": "fake"}


class FlakyS3Client(FakeS3Client):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def put_object(self, **kwargs: object) -> dict[str, object]:
        self.calls += 1
        if self.calls == 1:
            raise ClientError(
                error_response={"Error": {"Code": "Throttling", "Message": "retry me"}},
                operation_name="PutObject",
            )
        return super().put_object(**kwargs)


def build_paths() -> S3DataLakePaths:
    return S3DataLakePaths(
        bucket="fdp-dev-bucket",
        batch_raw_prefix="batch/raw",
        batch_rejected_prefix="batch/rejected",
        batch_silver_prefix="batch/silver",
        batch_gold_prefix="batch/gold",
        streaming_raw_prefix="streaming/raw",
        streaming_rejected_prefix="streaming/rejected",
        streaming_silver_prefix="streaming/silver",
        streaming_gold_prefix="streaming/gold",
        streaming_checkpoint_prefix="streaming/checkpoints",
    )


def test_validate_batch_filename_accepts_expected_pattern() -> None:
    dataset_name, source_format = validate_batch_filename("transactions_20260815T120000Z.csv")
    assert dataset_name == "transactions"
    assert source_format == "csv"


def test_validate_batch_filename_rejects_bad_pattern() -> None:
    with pytest.raises(ValueError):
        validate_batch_filename("transactions.csv")


def test_load_records_reads_json_list(tmp_path: Path) -> None:
    path = tmp_path / "customers_20260815T120000Z.json"
    path.write_text(json.dumps([{"customer_id": "CUST-1"}]), encoding="utf-8")
    records = load_records(path, "json")
    assert records == [{"customer_id": "CUST-1"}]


def test_validate_required_structure_rejects_empty_file() -> None:
    with pytest.raises(ValueError):
        validate_required_structure("customers", [])


def test_compute_file_checksum_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "customers_20260815T120000Z.json"
    path.write_text("hello", encoding="utf-8")
    assert compute_file_checksum(path) == compute_file_checksum(path)


def test_batch_ingestion_uploads_file_and_metadata(tmp_path: Path) -> None:
    path = tmp_path / "transactions_20260815T120000Z.json"
    path.write_text(json.dumps([{"transaction_id": "TXN-1"}]), encoding="utf-8")
    client = FakeS3Client()
    service = BatchIngestionService(client, build_paths())

    result = service.ingest_file(path)

    assert result.object_key == "batch/raw/transactions/transactions_20260815T120000Z.json"
    assert result.metadata_key == (
        "batch/raw/transactions/_metadata/transactions_20260815T120000Z.metadata.json"
    )
    assert len(client.objects) == 2


def test_batch_ingestion_retries_retryable_uploads(tmp_path: Path) -> None:
    path = tmp_path / "payments_20260815T120000Z.json"
    path.write_text(json.dumps([{"payment_id": "PAY-1"}]), encoding="utf-8")
    client = FlakyS3Client()
    service = BatchIngestionService(client, build_paths(), retries=2)

    result = service.ingest_file(path)

    assert result.dataset_name == "payments"
    assert client.calls >= 2
