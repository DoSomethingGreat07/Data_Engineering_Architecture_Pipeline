from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from src.common.schemas import SecurityRecord
from src.common.security import canonical_security_id_from_symbol
from src.sources.alpha_vantage_batch.models import (
    AlphaVantageNormalizedBundle,
    AlphaVantageRawBundle,
)


def map_alpha_vantage_bundle(
    raw_bundle: AlphaVantageRawBundle,
) -> AlphaVantageNormalizedBundle:
    extraction_time = datetime.now(UTC)
    securities = [
        map_security(record)
        for record in raw_bundle.listings
        if (record.get("symbol") or "").strip()
    ]
    security_overviews = [
        map_security_overview(symbol, overview)
        for symbol, overview in raw_bundle.overviews.items()
        if overview
    ]
    daily_prices = [
        price_record
        for symbol, series_payload in raw_bundle.daily_time_series.items()
        for price_record in map_daily_prices(symbol, series_payload)
    ]
    metadata = {
        "source_system": "alpha_vantage",
        "source_mode": "batch",
        "source_endpoint_or_file": "LISTING_STATUS + OVERVIEW + TIME_SERIES_DAILY",
        "source_record_id": raw_bundle.request_params.get("state", "active"),
        "ingestion_timestamp": extraction_time.isoformat(),
        "processing_timestamp": extraction_time.isoformat(),
        "ingestion_id": (
            "alpha-vantage-listing-status-"
            f"{extraction_time.strftime('%Y%m%dT%H%M%SZ')}"
        ),
        "raw_payload_checksum": compute_bundle_checksum(raw_bundle.model_dump(mode="json")),
        "raw_payload_location": "raw/alpha_vantage/",
        "schema_version": 1,
        "mapping_version": 1,
        "record_count": len(securities),
        "overview_count": len(security_overviews),
        "daily_price_count": len(daily_prices),
        "request_params": raw_bundle.request_params,
    }
    return AlphaVantageNormalizedBundle(
        securities=securities,
        security_overviews=security_overviews,
        daily_prices=daily_prices,
        metadata=metadata,
    )


def map_security(listing: dict[str, str]) -> dict[str, Any]:
    symbol = (listing.get("symbol") or "").strip().upper()
    security_name = (listing.get("name") or symbol or "UNKNOWN SECURITY").strip()
    exchange_code = (listing.get("exchange") or "UNKNOWN").strip().upper()
    security_type = normalize_security_type(listing.get("assetType"))
    record = SecurityRecord(
        security_id=canonical_security_id_from_symbol(symbol),
        ticker=symbol,
        security_name=security_name,
        security_type=security_type,
        exchange_code=exchange_code,
        currency_code="USD",
    )
    return record.model_dump(mode="json")


def normalize_security_type(asset_type: str | None) -> str:
    normalized = (asset_type or "").strip().upper()
    if not normalized:
        return "EQUITY"
    if normalized == "STOCK":
        return "EQUITY"
    return normalized.replace(" ", "_")


def map_security_overview(symbol: str, overview: dict[str, Any]) -> dict[str, Any]:
    return {
        "security_id": canonical_security_id_from_symbol(symbol),
        "ticker": symbol.strip().upper(),
        "security_name": overview.get("Name") or symbol.strip().upper(),
        "description": overview.get("Description") or "",
        "exchange_code": (overview.get("Exchange") or "UNKNOWN").strip().upper(),
        "currency_code": (overview.get("Currency") or "USD").strip().upper(),
        "country": (overview.get("Country") or "US").strip().upper(),
        "sector": overview.get("Sector") or "UNKNOWN",
        "industry": overview.get("Industry") or "UNKNOWN",
        "market_cap": _coerce_decimal(overview.get("MarketCapitalization")),
        "pe_ratio": _coerce_decimal(overview.get("PERatio")),
        "dividend_yield": _coerce_decimal(overview.get("DividendYield")),
        "beta": _coerce_decimal(overview.get("Beta")),
        "fiscal_year_end": overview.get("FiscalYearEnd") or "",
        "latest_quarter": overview.get("LatestQuarter") or "",
    }


def map_daily_prices(symbol: str, series_payload: dict[str, Any]) -> list[dict[str, Any]]:
    time_series = series_payload.get("Time Series (Daily)", {})
    if not isinstance(time_series, dict):
        return []
    records: list[dict[str, Any]] = []
    security_id = canonical_security_id_from_symbol(symbol)
    for trade_date, values in sorted(time_series.items()):
        if not isinstance(values, dict):
            continue
        records.append(
            {
                "security_id": security_id,
                "ticker": symbol.strip().upper(),
                "price_date": trade_date,
                "open_price": _coerce_decimal(values.get("1. open")),
                "high_price": _coerce_decimal(values.get("2. high")),
                "low_price": _coerce_decimal(values.get("3. low")),
                "close_price": _coerce_decimal(values.get("4. close")),
                "volume": int(str(values.get("5. volume") or "0")),
                "source_system": "alpha_vantage",
            }
        )
    return records


def _coerce_decimal(value: Any) -> str:
    if value in (None, "", "None"):
        return "0"
    return str(Decimal(str(value)))


def compute_bundle_checksum(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
