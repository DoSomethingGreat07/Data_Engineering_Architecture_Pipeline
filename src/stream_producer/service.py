from __future__ import annotations

import json
import logging
import signal
import time
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from src.common.retry import retry
from src.stream_producer.models import ProducerResult, ProducerSettings, StreamEvent

LOGGER = logging.getLogger(__name__)


class KinesisClientProtocol(Protocol):
    def put_record(self, **kwargs: Any) -> dict[str, Any]:
        """Write a record to Kinesis."""


class GracefulStopHandler:
    def __init__(self) -> None:
        self.stop_requested = False

    def install(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame: object | None) -> None:
        del frame
        LOGGER.info("received stop signal", extra={"signal": signum})
        self.stop_requested = True


def load_stream_events(path: str | Path) -> list[StreamEvent]:
    records: list[StreamEvent] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            event_type = payload["event_type"]
            event = StreamEvent(
                event_id=payload["event_id"],
                event_type=event_type,
                partition_key=payload["partition_key"],
                event_timestamp=datetime.fromisoformat(
                    payload["event_timestamp"].replace("Z", "+00:00")
                ),
                processing_timestamp=datetime.fromisoformat(
                    payload["processing_timestamp"].replace("Z", "+00:00")
                ),
                payload=payload,
                duplicate_flag=bool(payload.get("duplicate_flag", False)),
                late_arrival_flag=bool(payload.get("late_arrival_flag", False)),
            )
            records.append(event)
    return records


class KinesisProducerService:
    def __init__(
        self,
        client: KinesisClientProtocol,
        settings: ProducerSettings,
        stop_handler: GracefulStopHandler | None = None,
    ) -> None:
        self.client = client
        self.settings = settings
        self.stop_handler = stop_handler or GracefulStopHandler()

    def send_events(self, events: Iterable[StreamEvent]) -> ProducerResult:
        self.stop_handler.install()
        started_at = datetime.now(UTC)
        attempted = 0
        succeeded = 0
        failed = 0
        max_events = self.settings.finite_event_count
        delay_seconds = 1 / self.settings.events_per_second
        for event in events:
            if self.stop_handler.stop_requested:
                LOGGER.info("stopping producer gracefully at user request")
                break
            if max_events is not None and attempted >= max_events:
                break
            attempted += 1
            partition_key = event.partition_key
            payload_bytes = json.dumps(event.payload, default=_json_default).encode("utf-8")
            try:
                retry(
                    self._put_record_operation(partition_key, payload_bytes),
                    retries=3,
                )
                succeeded += 1
            except Exception as error:  # noqa: BLE001
                failed += 1
                LOGGER.exception(
                    "failed to send event to Kinesis",
                    extra={"event_id": event.event_id, "error": str(error)},
                )
            if self.settings.sleep_enabled and delay_seconds > 0:
                time.sleep(delay_seconds)
        return ProducerResult.create(
            attempted_records=attempted,
            successful_records=succeeded,
            failed_records=failed,
            started_at=started_at,
        )

    def _put_record_operation(
        self, partition_key: str, payload_bytes: bytes
    ) -> Callable[[], dict[str, Any]]:
        def operation() -> dict[str, Any]:
            return self.client.put_record(
                StreamName=self.settings.stream_name,
                PartitionKey=partition_key,
                Data=payload_bytes,
            )

        return operation


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    raise TypeError(f"Unsupported type for streaming payload: {type(value)!r}")
