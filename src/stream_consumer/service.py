from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

from src.stream_consumer.models import (
    ConsumedBatchPaths,
    ConsumedBatchResult,
    ConsumedRecord,
)


class KinesisClientProtocol(Protocol):
    def list_shards(self, **kwargs: object) -> dict[str, object]:
        ...

    def get_shard_iterator(self, **kwargs: object) -> dict[str, object]:
        ...

    def get_records(self, **kwargs: object) -> dict[str, object]:
        ...


class KinesisShardProtocol(Protocol):
    @property
    def ShardId(self) -> str:
        ...


@dataclass(frozen=True)
class ConsumeRequest:
    stream_name: str
    max_records: int
    iterator_type: str = "LATEST"
    poll_interval_seconds: float = 1.0
    max_empty_polls: int = 3


class KinesisStreamConsumerService:
    def __init__(self, client: KinesisClientProtocol) -> None:
        self._client = client

    def consume_to_directory(
        self,
        *,
        output_dir: Path,
        bronze_root: Path,
        request: ConsumeRequest,
    ) -> ConsumedBatchResult:
        records = self.consume(request)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

        raw_dir = output_dir / "raw" / "kinesis"
        canonical_dir = output_dir / "canonical" / "kinesis"
        bronze_dir = bronze_root / "events"
        raw_dir.mkdir(parents=True, exist_ok=True)
        canonical_dir.mkdir(parents=True, exist_ok=True)
        bronze_dir.mkdir(parents=True, exist_ok=True)

        raw_messages_path = raw_dir / f"kinesis_records_{timestamp}.json"
        canonical_events_path = canonical_dir / f"stream_events_{timestamp}.jsonl"
        bronze_events_path = bronze_dir / f"stream_events_{timestamp}.jsonl"

        raw_payload = [
            {
                "shard_id": record.shard_id,
                "partition_key": record.partition_key,
                "sequence_number": record.sequence_number,
                "approximate_arrival_timestamp": record.approximate_arrival_timestamp,
                "parse_failed": record.parse_failed,
                "raw_data": record.raw_data,
                "payload": record.payload,
            }
            for record in records
        ]
        raw_messages_path.write_text(json.dumps(raw_payload, indent=2), encoding="utf-8")

        parsed_lines = [
            json.dumps(record.payload, default=str)
            for record in records
            if record.payload is not None and not record.parse_failed
        ]
        canonical_text = "\n".join(parsed_lines)
        if canonical_text:
            canonical_text += "\n"
        canonical_events_path.write_text(canonical_text, encoding="utf-8")
        bronze_events_path.write_text(canonical_text, encoding="utf-8")

        parsed_records = sum(
            1
            for record in records
            if record.payload is not None and not record.parse_failed
        )
        parse_failures = sum(1 for record in records if record.parse_failed)
        return ConsumedBatchResult(
            paths=ConsumedBatchPaths(
                raw_messages_path=raw_messages_path,
                canonical_events_path=canonical_events_path,
                bronze_events_path=bronze_events_path,
            ),
            records_read=len(records),
            parsed_records=parsed_records,
            parse_failures=parse_failures,
        )

    def consume(self, request: ConsumeRequest) -> list[ConsumedRecord]:
        shard_ids = self._list_shards(request.stream_name)
        records: list[ConsumedRecord] = []
        for shard_id in shard_ids:
            records.extend(
                self._consume_shard(
                    shard_id,
                    request,
                    remaining=request.max_records - len(records),
                )
            )
            if len(records) >= request.max_records:
                break
        return records[: request.max_records]

    def _list_shards(self, stream_name: str) -> list[str]:
        response = self._client.list_shards(StreamName=stream_name)
        shards = cast(list[dict[str, Any]], response.get("Shards", []))
        return [str(shard["ShardId"]) for shard in shards if "ShardId" in shard]

    def _consume_shard(
        self,
        shard_id: str,
        request: ConsumeRequest,
        *,
        remaining: int,
    ) -> list[ConsumedRecord]:
        if remaining <= 0:
            return []
        iterator_response = self._client.get_shard_iterator(
            StreamName=request.stream_name,
            ShardId=shard_id,
            ShardIteratorType=request.iterator_type,
        )
        iterator = iterator_response.get("ShardIterator")
        if not iterator:
            return []

        empty_polls = 0
        collected: list[ConsumedRecord] = []
        while iterator and len(collected) < remaining and empty_polls < request.max_empty_polls:
            response = self._client.get_records(
                ShardIterator=iterator,
                Limit=min(remaining - len(collected), 1000),
            )
            iterator = response.get("NextShardIterator")
            raw_records = cast(list[dict[str, Any]], response.get("Records", []))
            if not raw_records:
                empty_polls += 1
                time.sleep(request.poll_interval_seconds)
                continue
            empty_polls = 0
            for raw_record in raw_records:
                data = raw_record.get("Data", b"")
                if isinstance(data, bytes):
                    text = data.decode("utf-8")
                else:
                    text = str(data)
                payload, parse_failed = self._parse_payload(text)
                arrival_timestamp = raw_record.get("ApproximateArrivalTimestamp")
                collected.append(
                    ConsumedRecord(
                        shard_id=shard_id,
                        partition_key=str(raw_record.get("PartitionKey", "")),
                        sequence_number=str(raw_record.get("SequenceNumber", "")),
                        raw_data=text,
                        payload=payload,
                        parse_failed=parse_failed,
                        approximate_arrival_timestamp=(
                            arrival_timestamp.astimezone(UTC).isoformat()
                            if isinstance(arrival_timestamp, datetime)
                            else str(arrival_timestamp)
                            if arrival_timestamp is not None
                            else None
                        ),
                    )
                )
                if len(collected) >= remaining:
                    break
        return collected

    def _parse_payload(self, text: str) -> tuple[dict[str, object] | None, bool]:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None, True
        if not isinstance(payload, dict):
            return None, True
        return payload, False
