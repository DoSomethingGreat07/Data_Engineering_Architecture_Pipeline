from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.common.logging_utils import configure_logging
from src.sources.alpha_vantage_batch.client import AlphaVantageBatchClient
from src.sources.alpha_vantage_batch.service import (
    AlphaVantageBatchExtractionService,
    build_alpha_vantage_config_from_env,
)

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract Alpha Vantage reference listings and normalize them."
    )
    parser.add_argument("--output-dir", default="data/external_sources")
    parser.add_argument("--date", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--daily-outputsize", default=None)
    parser.add_argument("--skip-overview", action="store_true")
    parser.add_argument("--skip-daily-prices", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.log_level)
    config = build_alpha_vantage_config_from_env()
    if not config.api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY is required")

    client = AlphaVantageBatchClient(config)
    service = AlphaVantageBatchExtractionService(client)
    symbols = args.symbols.split(",") if args.symbols else None
    raw_bundle = service.fetch_raw_bundle(
        date=args.date,
        state=args.state,
        symbols=symbols,
        include_overview=not args.skip_overview,
        include_daily_prices=not args.skip_daily_prices,
        daily_outputsize=args.daily_outputsize,
    )
    normalized_bundle = service.normalize(raw_bundle)
    paths = service.write_bundle(
        output_dir=Path(args.output_dir),
        raw_bundle=raw_bundle,
        normalized_bundle=normalized_bundle,
    )
    LOGGER.info(
        "alpha vantage batch extraction complete",
        extra={
            "raw_listings_path": str(paths.raw_listings_path),
            "canonical_securities_path": str(paths.canonical_securities_path),
            "record_count": len(normalized_bundle.securities),
            "overview_count": len(normalized_bundle.security_overviews),
            "daily_price_count": len(normalized_bundle.daily_prices),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
