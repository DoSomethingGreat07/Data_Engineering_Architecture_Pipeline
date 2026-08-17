from __future__ import annotations

import json
from pathlib import Path

from src.sources.alpaca_streaming.client import AlpacaStreamingClient, run_stream_capture
from src.sources.alpaca_streaming.mapper import map_alpaca_trade_to_stream_event
from src.sources.alpaca_streaming.models import (
    AlpacaStreamCaptureRequest,
    AlpacaStreamCaptureResult,
    AlpacaStreamConfig,
    AlpacaStreamOutputPaths,
)
from src.stream_producer.models import StreamEvent


class AlpacaStreamingIngestionService:
    def __init__(self, client: AlpacaStreamingClient) -> None:
        self.client = client

    def capture(self, request: AlpacaStreamCaptureRequest) -> AlpacaStreamCaptureResult:
        raw_messages = run_stream_capture(
            self.client,
            subscription=request.subscription,
            max_messages=request.max_messages,
        )
        trade_messages = [message for message in raw_messages if message.get("T") == "t"]
        events = [
            map_alpaca_trade_to_stream_event(message, request.broker_context)
            for message in trade_messages
        ]
        return AlpacaStreamCaptureResult(events=events, raw_messages=raw_messages)

    def write_capture(
        self,
        *,
        output_dir: str | Path,
        capture_result: AlpacaStreamCaptureResult,
    ) -> AlpacaStreamOutputPaths:
        output_root = Path(output_dir)
        raw_dir = output_root / "raw" / "alpaca"
        canonical_dir = output_root / "streaming" / "alpaca"
        raw_dir.mkdir(parents=True, exist_ok=True)
        canonical_dir.mkdir(parents=True, exist_ok=True)

        suffix = (
            capture_result.events[0].processing_timestamp.strftime("%Y%m%dT%H%M%SZ")
            if capture_result.events
            else "empty"
        )
        raw_messages_path = raw_dir / f"market_data_{suffix}.json"
        canonical_events_path = canonical_dir / f"trade_events_{suffix}.jsonl"

        raw_messages_path.write_text(
            json.dumps(capture_result.raw_messages, indent=2),
            encoding="utf-8",
        )
        with canonical_events_path.open("w", encoding="utf-8") as handle:
            for event in capture_result.events:
                handle.write(json.dumps(event.payload, default=_json_default) + "\n")

        return AlpacaStreamOutputPaths(
            raw_messages_path=raw_messages_path,
            canonical_events_path=canonical_events_path,
        )

    def publish_to_kinesis(
        self,
        *,
        events: list[StreamEvent],
        stream_name: str,
        aws_region: str,
        aws_profile: str | None = None,
    ) -> int:
        import boto3

        session_kwargs: dict[str, str] = {"region_name": aws_region}
        if aws_profile:
            session_kwargs["profile_name"] = aws_profile
        session = boto3.Session(**session_kwargs)
        client = session.client("kinesis")
        published = 0
        for event in events:
            client.put_record(
                StreamName=stream_name,
                PartitionKey=event.partition_key,
                Data=json.dumps(event.payload, default=_json_default).encode("utf-8"),
            )
            published += 1
        return published


def build_alpaca_stream_config_from_env() -> AlpacaStreamConfig:
    import os

    return AlpacaStreamConfig(
        api_key_id=os.environ.get("ALPACA_API_KEY_ID", ""),
        api_secret_key=os.environ.get("ALPACA_API_SECRET_KEY", ""),
        base_url=os.environ.get("ALPACA_STREAM_BASE_URL", "wss://stream.data.alpaca.markets"),
        data_version=os.environ.get("ALPACA_STREAM_DATA_VERSION", "v2"),
        feed=os.environ.get("ALPACA_STREAM_FEED", "iex"),
        use_test_stream=os.environ.get("ALPACA_STREAM_USE_TEST", "false").lower() == "true",
    )


def _json_default(value: object) -> str:
    from datetime import datetime

    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    raise TypeError(f"unsupported value type: {type(value)!r}")
