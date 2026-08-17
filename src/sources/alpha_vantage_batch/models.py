from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AlphaVantageConfig(BaseModel):
    api_key: str
    base_url: str = "https://www.alphavantage.co/query"
    default_state: str = "active"
    default_daily_outputsize: str = "compact"


class AlphaVantageRawBundle(BaseModel):
    request_params: dict[str, Any]
    listings_csv: str
    listings: list[dict[str, str]]
    overviews: dict[str, dict[str, Any]] = Field(default_factory=dict)
    daily_time_series: dict[str, dict[str, Any]] = Field(default_factory=dict)


class AlphaVantageNormalizedBundle(BaseModel):
    securities: list[dict[str, Any]]
    security_overviews: list[dict[str, Any]]
    daily_prices: list[dict[str, Any]]
    metadata: dict[str, Any]


class AlphaVantageOutputPaths(BaseModel):
    raw_listings_path: Path
    raw_overviews_path: Path
    raw_daily_prices_path: Path
    canonical_securities_path: Path
    canonical_overviews_path: Path
    canonical_daily_prices_path: Path
    metadata_path: Path
