from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class BatchIngestionMetadata(BaseModel):
    dataset_name: str
    filename: str
    source_path: str
    source_format: str
    source_row_count: int = Field(ge=0)
    ingestion_id: str
    ingestion_timestamp: datetime
    source_checksum: str

    @classmethod
    def create(
        cls,
        dataset_name: str,
        filename: str,
        source_path: str,
        source_format: str,
        source_row_count: int,
        source_checksum: str,
    ) -> BatchIngestionMetadata:
        timestamp = datetime.now(UTC)
        return cls(
            dataset_name=dataset_name,
            filename=filename,
            source_path=source_path,
            source_format=source_format,
            source_row_count=source_row_count,
            ingestion_id=f"{dataset_name}-{timestamp.strftime('%Y%m%dT%H%M%SZ')}",
            ingestion_timestamp=timestamp,
            source_checksum=source_checksum,
        )


class BatchUploadResult(BaseModel):
    bucket: str
    object_key: str
    metadata_key: str
    dataset_name: str
    row_count: int
    checksum: str
