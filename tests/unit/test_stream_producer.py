import json
from pathlib import Path

from botocore.exceptions import ClientError

from src.stream_producer.models import ProducerSettings
from src.stream_producer.service import (
    GracefulStopHandler,
    KinesisProducerService,
    load_stream_events,
)


class FakeKinesisClient:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def put_record(self, **kwargs: object) -> dict[str, object]:
        self.records.append(kwargs)
        return {"SequenceNumber": "1"}


class FlakyKinesisClient(FakeKinesisClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def put_record(self, **kwargs: object) -> dict[str, object]:
        self.calls += 1
        if self.calls == 1:
            raise ClientError(
                error_response={"Error": {"Code": "Throttling", "Message": "retry me"}},
                operation_name="PutRecord",
            )
        return super().put_record(**kwargs)


class PreStoppedHandler(GracefulStopHandler):
    def install(self) -> None:
        self.stop_requested = True


def test_load_stream_events_parses_generated_shape(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps(
            {
                "event_id": "EVT-1",
                "event_type": "transaction",
                "partition_key": "ACCT-1",
                "event_timestamp": "2026-08-15T12:00:00Z",
                "processing_timestamp": "2026-08-15T12:00:05Z",
                "transaction_id": "TXN-1",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    events = load_stream_events(path)

    assert len(events) == 1
    assert events[0].partition_key == "ACCT-1"
    assert events[0].payload["transaction_id"] == "TXN-1"


def test_kinesis_producer_sends_finite_number_of_events(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    lines = [
        {
            "event_id": f"EVT-{index}",
            "event_type": "transaction",
            "partition_key": f"ACCT-{index}",
            "event_timestamp": "2026-08-15T12:00:00Z",
            "processing_timestamp": "2026-08-15T12:00:05Z",
            "transaction_id": f"TXN-{index}",
        }
        for index in range(3)
    ]
    path.write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")
    client = FakeKinesisClient()
    service = KinesisProducerService(
        client,
        ProducerSettings(
            stream_name="fdp-dev-events",
            events_per_second=100,
            finite_event_count=2,
            sleep_enabled=False,
        ),
    )

    result = service.send_events(load_stream_events(path))

    assert result.attempted_records == 2
    assert result.successful_records == 2
    assert len(client.records) == 2


def test_kinesis_producer_retries_retryable_failures(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps(
            {
                "event_id": "EVT-1",
                "event_type": "transaction",
                "partition_key": "ACCT-1",
                "event_timestamp": "2026-08-15T12:00:00Z",
                "processing_timestamp": "2026-08-15T12:00:05Z",
                "transaction_id": "TXN-1",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    client = FlakyKinesisClient()
    service = KinesisProducerService(
        client,
        ProducerSettings(
            stream_name="fdp-dev-events",
            events_per_second=100,
            finite_event_count=1,
            sleep_enabled=False,
        ),
    )

    result = service.send_events(load_stream_events(path))

    assert result.successful_records == 1
    assert client.calls >= 2


def test_kinesis_producer_stops_gracefully_when_requested(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps(
            {
                "event_id": "EVT-1",
                "event_type": "transaction",
                "partition_key": "ACCT-1",
                "event_timestamp": "2026-08-15T12:00:00Z",
                "processing_timestamp": "2026-08-15T12:00:05Z",
                "transaction_id": "TXN-1",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    client = FakeKinesisClient()
    service = KinesisProducerService(
        client,
        ProducerSettings(
            stream_name="fdp-dev-events",
            events_per_second=100,
            finite_event_count=1,
            sleep_enabled=False,
        ),
        stop_handler=PreStoppedHandler(),
    )

    result = service.send_events(load_stream_events(path))

    assert result.attempted_records == 0
    assert result.successful_records == 0

