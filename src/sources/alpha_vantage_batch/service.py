from __future__ import annotations

import json
from pathlib import Path

from src.sources.alpha_vantage_batch.client import AlphaVantageBatchClient
from src.sources.alpha_vantage_batch.mapper import map_alpha_vantage_bundle
from src.sources.alpha_vantage_batch.models import (
    AlphaVantageConfig,
    AlphaVantageNormalizedBundle,
    AlphaVantageOutputPaths,
    AlphaVantageRawBundle,
)


class AlphaVantageBatchExtractionService:
    def __init__(self, client: AlphaVantageBatchClient) -> None:
        self.client = client

    def fetch_raw_bundle(
        self,
        *,
        date: str | None = None,
        state: str | None = None,
        symbols: list[str] | None = None,
        include_overview: bool = True,
        include_daily_prices: bool = True,
        daily_outputsize: str | None = None,
    ) -> AlphaVantageRawBundle:
        listings_csv, listings, request_params = self.client.get_listing_status(
            date=date,
            state=state,
        )
        enrichment_symbols: list[str] = []
        if symbols:
            allowed = {symbol.strip().upper() for symbol in symbols if symbol.strip()}
            listings = [row for row in listings if (row.get("symbol") or "").upper() in allowed]
            enrichment_symbols = sorted(allowed)
        overviews = (
            {
                symbol: self.client.get_company_overview(symbol)
                for symbol in enrichment_symbols
            }
            if include_overview
            else {}
        )
        daily_time_series = (
            {
                symbol: self.client.get_daily_time_series(
                    symbol,
                    outputsize=daily_outputsize,
                )
                for symbol in enrichment_symbols
            }
            if include_daily_prices
            else {}
        )
        return AlphaVantageRawBundle(
            request_params=request_params,
            listings_csv=listings_csv,
            listings=listings,
            overviews=overviews,
            daily_time_series=daily_time_series,
        )

    def normalize(self, raw_bundle: AlphaVantageRawBundle) -> AlphaVantageNormalizedBundle:
        return map_alpha_vantage_bundle(raw_bundle)

    def write_bundle(
        self,
        *,
        output_dir: str | Path,
        raw_bundle: AlphaVantageRawBundle,
        normalized_bundle: AlphaVantageNormalizedBundle,
    ) -> AlphaVantageOutputPaths:
        output_root = Path(output_dir)
        raw_dir = output_root / "raw" / "alpha_vantage"
        canonical_dir = output_root / "canonical" / "alpha_vantage"
        raw_dir.mkdir(parents=True, exist_ok=True)
        canonical_dir.mkdir(parents=True, exist_ok=True)

        timestamp = normalized_bundle.metadata["ingestion_id"].rsplit("-", 1)[-1]
        raw_listings_path = raw_dir / f"listing_status_{timestamp}.csv"
        raw_overviews_path = raw_dir / f"overview_{timestamp}.json"
        raw_daily_prices_path = raw_dir / f"daily_prices_{timestamp}.json"
        canonical_securities_path = canonical_dir / f"securities_{timestamp}.json"
        canonical_overviews_path = canonical_dir / f"security_overviews_{timestamp}.json"
        canonical_daily_prices_path = canonical_dir / f"daily_prices_{timestamp}.json"
        metadata_path = canonical_dir / f"alpha_vantage_metadata_{timestamp}.json"

        raw_listings_path.write_text(raw_bundle.listings_csv, encoding="utf-8")
        raw_overviews_path.write_text(
            json.dumps(raw_bundle.overviews, indent=2),
            encoding="utf-8",
        )
        raw_daily_prices_path.write_text(
            json.dumps(raw_bundle.daily_time_series, indent=2),
            encoding="utf-8",
        )
        canonical_securities_path.write_text(
            json.dumps(normalized_bundle.securities, indent=2),
            encoding="utf-8",
        )
        canonical_overviews_path.write_text(
            json.dumps(normalized_bundle.security_overviews, indent=2),
            encoding="utf-8",
        )
        canonical_daily_prices_path.write_text(
            json.dumps(normalized_bundle.daily_prices, indent=2),
            encoding="utf-8",
        )
        metadata_path.write_text(
            json.dumps(normalized_bundle.metadata, indent=2),
            encoding="utf-8",
        )

        return AlphaVantageOutputPaths(
            raw_listings_path=raw_listings_path,
            raw_overviews_path=raw_overviews_path,
            raw_daily_prices_path=raw_daily_prices_path,
            canonical_securities_path=canonical_securities_path,
            canonical_overviews_path=canonical_overviews_path,
            canonical_daily_prices_path=canonical_daily_prices_path,
            metadata_path=metadata_path,
        )


def build_alpha_vantage_config_from_env() -> AlphaVantageConfig:
    import os

    return AlphaVantageConfig(
        api_key=os.environ.get("ALPHA_VANTAGE_API_KEY", ""),
        default_state=os.environ.get("ALPHA_VANTAGE_DEFAULT_STATE", "active"),
        default_daily_outputsize=os.environ.get(
            "ALPHA_VANTAGE_DAILY_OUTPUTSIZE",
            "compact",
        ),
    )
