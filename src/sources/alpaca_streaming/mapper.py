from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from src.common.schemas import TradeRecord
from src.common.security import canonical_security_id_from_symbol
from src.sources.alpaca_streaming.models import BrokerContext
from src.stream_producer.models import StreamEvent


def map_alpaca_trade_to_stream_event(
    payload: dict[str, Any],
    broker_context: BrokerContext,
) -> StreamEvent:
    symbol = str(payload.get("S") or "").strip().upper()
    event_timestamp = _coerce_datetime(payload.get("t"))
    processing_timestamp = datetime.now(UTC)
    trade_id = build_trade_id(payload)
    quantity = Decimal(str(payload.get("s", 0)))
    price = Decimal(str(payload.get("p", 0)))
    trade_record = TradeRecord(
        trade_id=trade_id,
        account_id=broker_context.account_id,
        customer_id=broker_context.customer_id,
        security_id=canonical_security_id_from_symbol(symbol),
        quantity=quantity,
        price=price,
        transaction_amount=(quantity * price),
        currency_code="USD",
        side=derive_trade_side(payload),
        transaction_status="POSTED",
        event_timestamp=event_timestamp,
        processing_timestamp=processing_timestamp,
        country_code=broker_context.country_code,
        risk_score=derive_trade_risk_score(payload, broker_context.risk_score),
    )
    record_payload = trade_record.model_dump(mode="json")
    event_id = f"EVT-{trade_id}"
    return StreamEvent(
        event_id=event_id,
        event_type="trade",
        partition_key=record_payload["security_id"],
        event_timestamp=event_timestamp,
        processing_timestamp=processing_timestamp,
        payload={
            "event_id": event_id,
            "event_type": "trade",
            "partition_key": record_payload["security_id"],
            "event_timestamp": event_timestamp,
            "processing_timestamp": processing_timestamp,
            **record_payload,
        },
    )


def build_trade_id(payload: dict[str, Any]) -> str:
    symbol = str(payload.get("S") or "UNKNOWN").strip().upper()
    exchange = str(payload.get("x") or "UNK").strip().upper()
    trade_key = payload.get("i") or payload.get("t") or "NOID"
    return f"ALPACA-{symbol}-{exchange}-{trade_key}"


def derive_trade_side(payload: dict[str, Any]) -> str:
    taker_side = str(payload.get("tks") or "").upper()
    if taker_side == "B":
        return "BUY"
    if taker_side == "S":
        return "SELL"
    conditions = [str(value).upper() for value in payload.get("c", [])]
    if any("B" in value for value in conditions):
        return "BUY"
    return "SELL"


def derive_trade_risk_score(payload: dict[str, Any], default_score: int) -> int:
    score = default_score
    size = int(payload.get("s", 0) or 0)
    price = float(payload.get("p", 0) or 0)
    supported_tapes = {"A", "B", "C", "D", "J", "K", "N", "P", "Q", "V", "Z"}
    if size >= 100:
        score += 10
    if price * size >= 10000:
        score += 15
    if str(payload.get("z") or "").upper() not in supported_tapes:
        score += 5
    return min(score, 100)


def _coerce_datetime(value: Any) -> datetime:
    if not value:
        return datetime.now(UTC)
    text = str(value)
    return datetime.fromisoformat(text.replace("Z", "+00:00"))
