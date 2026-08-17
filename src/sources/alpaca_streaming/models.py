from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.stream_producer.models import StreamEvent


class AlpacaStreamConfig(BaseModel):
    api_key_id: str
    api_secret_key: str
    base_url: str = "wss://stream.data.alpaca.markets"
    data_version: str = "v2"
    feed: str = "iex"
    use_test_stream: bool = False

    @property
    def stream_url(self) -> str:
        if self.use_test_stream:
            return f"{self.base_url}/{self.data_version}/test"
        return f"{self.base_url}/{self.data_version}/{self.feed}"

    @property
    def latest_trades_url(self) -> str:
        if self.data_version == "v1beta3" and self.feed.startswith("crypto/"):
            loc = self.feed.split("/", 1)[1]
            return f"https://data.alpaca.markets/{self.data_version}/crypto/{loc}/latest/trades"
        raise ValueError("latest trades fallback is only configured for Alpaca crypto feeds")


class BrokerContext(BaseModel):
    account_id: str
    customer_id: str
    country_code: str = "US"
    risk_score: int = Field(default=20, ge=0, le=100)


class AlpacaStreamSubscription(BaseModel):
    symbols: list[str]
    channels: list[str] = Field(default_factory=lambda: ["trades"])


class AlpacaStreamCaptureRequest(BaseModel):
    subscription: AlpacaStreamSubscription
    broker_context: BrokerContext
    max_messages: int | None = Field(default=None, ge=1)


class AlpacaRawEvent(BaseModel):
    payload: dict[str, Any]


class AlpacaStreamCaptureResult(BaseModel):
    events: list[StreamEvent]
    raw_messages: list[dict[str, Any]]


class AlpacaStreamOutputPaths(BaseModel):
    raw_messages_path: Path
    canonical_events_path: Path
