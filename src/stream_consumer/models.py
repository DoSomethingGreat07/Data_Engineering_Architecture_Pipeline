from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConsumedRecord:
    shard_id: str
    partition_key: str
    sequence_number: str
    raw_data: str
    payload: dict[str, object] | None
    parse_failed: bool
    approximate_arrival_timestamp: str | None


@dataclass(frozen=True)
class ConsumedBatchPaths:
    raw_messages_path: Path
    canonical_events_path: Path
    bronze_events_path: Path


@dataclass(frozen=True)
class ConsumedBatchResult:
    paths: ConsumedBatchPaths
    records_read: int
    parsed_records: int
    parse_failures: int

