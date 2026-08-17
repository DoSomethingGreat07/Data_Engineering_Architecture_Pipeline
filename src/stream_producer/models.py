from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class StreamEvent(BaseModel):
    event_id: str
    event_type: str
    partition_key: str
    event_timestamp: datetime
    processing_timestamp: datetime
    payload: dict[str, Any]
    duplicate_flag: bool = False
    late_arrival_flag: bool = False


class ProducerResult(BaseModel):
    attempted_records: int = Field(ge=0)
    successful_records: int = Field(ge=0)
    failed_records: int = Field(ge=0)
    started_at: datetime
    finished_at: datetime

    @classmethod
    def create(
        cls,
        attempted_records: int,
        successful_records: int,
        failed_records: int,
        started_at: datetime,
    ) -> ProducerResult:
        return cls(
            attempted_records=attempted_records,
            successful_records=successful_records,
            failed_records=failed_records,
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )


@dataclass(frozen=True)
class ProducerSettings:
    stream_name: str
    events_per_second: int
    finite_event_count: int | None = None
    sleep_enabled: bool = True
