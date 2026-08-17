from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any, Protocol, cast

import requests

from src.sources.alpaca_streaming.models import AlpacaStreamConfig, AlpacaStreamSubscription


class WebSocketProtocol(Protocol):
    async def send(self, message: str) -> None:
        """Send a websocket message."""

    async def recv(self) -> str:
        """Receive a websocket message."""

    async def close(self) -> None:
        """Close the websocket."""


class ConnectContextProtocol(Protocol):
    async def __aenter__(self) -> Any:
        """Enter async connection context."""

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> Any:
        """Exit async connection context."""


class AlpacaStreamingClient:
    def __init__(self, config: AlpacaStreamConfig) -> None:
        self.config = config

    async def stream_messages(
        self,
        *,
        subscription: AlpacaStreamSubscription,
        max_messages: int | None = None,
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        count = 0
        async with self._connect() as websocket:
            await websocket.recv()
            await websocket.send(
                json.dumps(
                    {
                        "action": "auth",
                        "key": self.config.api_key_id,
                        "secret": self.config.api_secret_key,
                    }
                )
            )
            await websocket.recv()
            await websocket.send(
                json.dumps(
                    {
                        "action": "subscribe",
                        **{
                            channel: subscription.symbols
                            for channel in subscription.channels
                        },
                    }
                )
            )
            await websocket.recv()
            while True:
                raw_message = await websocket.recv()
                for payload in self._decode_message(raw_message):
                    if payload.get("T") in {"success", "subscription"}:
                        continue
                    messages.append(payload)
                    count += 1
                    if max_messages is not None and count >= max_messages:
                        return messages

    async def iter_messages(
        self,
        *,
        subscription: AlpacaStreamSubscription,
        max_messages: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        buffered = await self.stream_messages(
            subscription=subscription,
            max_messages=max_messages,
        )
        for message in buffered:
            yield message

    def _connect(self) -> ConnectContextProtocol:
        import websockets  # type: ignore[import-not-found]

        return cast(ConnectContextProtocol, websockets.connect(self.config.stream_url))

    def fetch_latest_trade_messages(
        self,
        *,
        subscription: AlpacaStreamSubscription,
    ) -> list[dict[str, Any]]:
        response = requests.get(
            self.config.latest_trades_url,
            headers={
                "APCA-API-KEY-ID": self.config.api_key_id,
                "APCA-API-SECRET-KEY": self.config.api_secret_key,
            },
            params={"symbols": ",".join(subscription.symbols)},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        trades = payload.get("trades", {})
        if not isinstance(trades, dict):
            raise ValueError("unexpected latest trades payload from Alpaca")

        normalized: list[dict[str, Any]] = []
        for symbol, trade in trades.items():
            if not isinstance(trade, dict):
                continue
            normalized.append(
                {
                    "T": "t",
                    "S": symbol,
                    **trade,
                }
            )
        return normalized

    @staticmethod
    def _decode_message(raw_message: str) -> list[dict[str, Any]]:
        payload = json.loads(raw_message)
        if isinstance(payload, dict):
            return [payload]
        if isinstance(payload, list):
            decoded = [item for item in payload if isinstance(item, dict)]
            return decoded
        raise ValueError("unexpected websocket payload type from Alpaca")


def run_stream_capture(
    client: AlpacaStreamingClient,
    *,
    subscription: AlpacaStreamSubscription,
    max_messages: int | None = None,
) -> list[dict[str, Any]]:
    try:
        return asyncio.run(
            client.stream_messages(subscription=subscription, max_messages=max_messages)
        )
    except Exception:
        return client.fetch_latest_trade_messages(subscription=subscription)
