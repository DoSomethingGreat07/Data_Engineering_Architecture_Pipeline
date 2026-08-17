import json
from datetime import UTC, datetime
from pathlib import Path

from src.sources.alpaca_streaming.mapper import (
    build_trade_id,
    derive_trade_risk_score,
    map_alpaca_trade_to_stream_event,
)
from src.sources.alpaca_streaming.models import (
    AlpacaStreamCaptureResult,
    AlpacaStreamConfig,
    BrokerContext,
)
from src.sources.alpaca_streaming.service import AlpacaStreamingIngestionService


class StubStreamingClient:
    def __init__(self, raw_messages: list[dict[str, object]]) -> None:
        self.raw_messages = raw_messages

    def fetch_latest_trade_messages(self, *, subscription: object) -> list[dict[str, object]]:
        del subscription
        return self.raw_messages


def build_broker_context() -> BrokerContext:
    return BrokerContext(
        account_id="ACCT-NFCU-BROKERAGE-001",
        customer_id="CUST-NFCU-BROKERAGE-001",
        country_code="US",
        risk_score=20,
    )


def build_trade_payload() -> dict[str, object]:
    return {
        "T": "t",
        "S": "AAPL",
        "i": 628,
        "x": "K",
        "p": 162.92,
        "s": 3,
        "c": ["@", "F", "T", "I"],
        "z": "C",
        "t": "2026-08-15T12:00:00.000000Z",
    }


def test_map_alpaca_trade_to_stream_event_creates_trade_payload() -> None:
    event = map_alpaca_trade_to_stream_event(build_trade_payload(), build_broker_context())
    assert event.event_type == "trade"
    assert event.partition_key == "SEC-AAPL"
    assert event.payload["trade_id"].startswith("ALPACA-AAPL-K-")
    assert event.payload["security_id"] == "SEC-AAPL"
    assert event.payload["transaction_amount"] == "488.76"


def test_build_trade_id_is_stable() -> None:
    assert build_trade_id(build_trade_payload()) == "ALPACA-AAPL-K-628"


def test_derive_trade_risk_score_increases_for_large_trade() -> None:
    low = derive_trade_risk_score({"s": 1, "p": 10, "z": "C"}, 20)
    high = derive_trade_risk_score({"s": 500, "p": 250, "z": "?"}, 20)
    assert high > low


def test_stream_config_uses_test_url_when_enabled() -> None:
    config = AlpacaStreamConfig(
        api_key_id="key",
        api_secret_key="secret",
        use_test_stream=True,
    )
    assert config.stream_url.endswith("/v2/test")


def test_write_capture_creates_files(tmp_path: Path) -> None:
    service = AlpacaStreamingIngestionService(client=StubStreamingClient([]))  # type: ignore[arg-type]
    event = map_alpaca_trade_to_stream_event(build_trade_payload(), build_broker_context())
    event = event.model_copy(
        update={"processing_timestamp": datetime(2026, 8, 15, 12, 0, tzinfo=UTC)}
    )
    capture_result = AlpacaStreamCaptureResult(
        events=[event],
        raw_messages=[build_trade_payload()],
    )
    paths = service.write_capture(output_dir=tmp_path, capture_result=capture_result)
    assert paths.raw_messages_path.exists()
    assert paths.canonical_events_path.exists()
    line = paths.canonical_events_path.read_text(encoding="utf-8").strip()
    assert json.loads(line)["security_id"] == "SEC-AAPL"


def test_crypto_latest_trade_side_uses_taker_side() -> None:
    payload = {
        "T": "t",
        "S": "BTC/USD",
        "i": 123,
        "p": 63539.2,
        "s": 0.5,
        "t": "2026-08-17T06:14:44.860184391Z",
        "tks": "B",
    }
    event = map_alpaca_trade_to_stream_event(payload, build_broker_context())
    assert event.payload["side"] == "BUY"
