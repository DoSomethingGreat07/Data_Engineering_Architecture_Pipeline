from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from src.batch_producer.models import BatchIngestionMetadata, BatchUploadResult
from src.batch_producer.validation import (
    compute_file_checksum,
    load_records,
    validate_batch_filename,
    validate_required_structure,
)
from src.common.retry import retry
from src.common.storage import S3DataLakePaths


class S3ClientProtocol(Protocol):
    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        """Upload an object to S3."""


class BatchIngestionService:
    def __init__(
        self,
        s3_client: S3ClientProtocol,
        data_lake_paths: S3DataLakePaths,
        retries: int = 3,
    ) -> None:
        self.s3_client = s3_client
        self.data_lake_paths = data_lake_paths
        self.retries = retries

    def ingest_file(self, source_path: str | Path) -> BatchUploadResult:
        path = Path(source_path)
        dataset_name, source_format = validate_batch_filename(path)
        records = load_records(path, source_format)
        row_count = validate_required_structure(dataset_name, records)
        checksum = compute_file_checksum(path)
        metadata = BatchIngestionMetadata.create(
            dataset_name=dataset_name,
            filename=path.name,
            source_path=str(path),
            source_format=source_format,
            source_row_count=row_count,
            source_checksum=checksum,
        )
        object_key = self.data_lake_paths.batch_raw_key(dataset_name, path.name)
        metadata_key = self.data_lake_paths.batch_raw_metadata_key(
            dataset_name,
            f"{path.stem}.metadata.json",
        )

        retry(
            lambda: self.s3_client.put_object(
                Bucket=self.data_lake_paths.bucket,
                Key=object_key,
                Body=path.read_bytes(),
                ContentType=self._content_type(source_format),
                Metadata={
                    "dataset_name": metadata.dataset_name,
                    "ingestion_id": metadata.ingestion_id,
                    "source_format": metadata.source_format,
                    "source_row_count": str(metadata.source_row_count),
                    "source_checksum": metadata.source_checksum,
                },
            ),
            retries=self.retries,
        )
        retry(
            lambda: self.s3_client.put_object(
                Bucket=self.data_lake_paths.bucket,
                Key=metadata_key,
                Body=json.dumps(metadata.model_dump(mode="json"), indent=2).encode("utf-8"),
                ContentType="application/json",
            ),
            retries=self.retries,
        )
        return BatchUploadResult(
            bucket=self.data_lake_paths.bucket,
            object_key=object_key,
            metadata_key=metadata_key,
            dataset_name=dataset_name,
            row_count=row_count,
            checksum=checksum,
        )

    @staticmethod
    def _content_type(source_format: str) -> str:
        if source_format == "csv":
            return "text/csv"
        return "application/json"
