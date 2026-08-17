from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.common.logging_utils import configure_logging
from src.sources.alpaca_streaming.client import AlpacaStreamingClient
from src.sources.alpaca_streaming.models import (
    AlpacaStreamCaptureRequest,
    AlpacaStreamSubscription,
    BrokerContext,
)
from src.sources.alpaca_streaming.service import (
    AlpacaStreamingIngestionService,
    build_alpaca_stream_config_from_env,
)

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture Alpaca real-time market data and normalize it to trade events."
    )
    parser.add_argument("--output-dir", default="data/external_sources")
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--max-messages", type=int, default=25)
    parser.add_argument("--kinesis-stream-name", default=None)
    parser.add_argument("--aws-region", default=None)
    parser.add_argument("--aws-profile", default=None)
    parser.add_argument("--account-id", default=None)
    parser.add_argument("--customer-id", default=None)
    parser.add_argument("--country-code", default=None)
    parser.add_argument("--risk-score", type=int, default=None)
    parser.add_argument("--log-level", default="INFO")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.log_level)
    config = build_alpaca_stream_config_from_env()
    if not config.api_key_id or not config.api_secret_key:
        raise ValueError("ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY are required")

    import os

    symbols_arg = args.symbols or os.environ.get("ALPACA_STREAM_SYMBOLS", "")
    symbols = [symbol.strip().upper() for symbol in symbols_arg.split(",") if symbol.strip()]
    if config.use_test_stream and not symbols:
        symbols = ["FAKEPACA"]
    if not symbols:
        raise ValueError("at least one Alpaca symbol is required")

    broker_context = BrokerContext(
        account_id=args.account_id or os.environ.get("ALPACA_BROKER_ACCOUNT_ID", ""),
        customer_id=args.customer_id or os.environ.get("ALPACA_BROKER_CUSTOMER_ID", ""),
        country_code=args.country_code or os.environ.get("ALPACA_COUNTRY_CODE", "US"),
        risk_score=args.risk_score or int(os.environ.get("ALPACA_RISK_SCORE", "20")),
    )
    if not broker_context.account_id or not broker_context.customer_id:
        raise ValueError("broker account and customer context are required for trade normalization")

    service = AlpacaStreamingIngestionService(AlpacaStreamingClient(config))
    capture_result = service.capture(
        AlpacaStreamCaptureRequest(
            subscription=AlpacaStreamSubscription(symbols=symbols),
            broker_context=broker_context,
            max_messages=args.max_messages,
        )
    )
    paths = service.write_capture(
        output_dir=Path(args.output_dir),
        capture_result=capture_result,
    )

    published = 0
    if args.kinesis_stream_name:
        if not args.aws_region:
            raise ValueError("--aws-region is required when --kinesis-stream-name is set")
        published = service.publish_to_kinesis(
            events=capture_result.events,
            stream_name=args.kinesis_stream_name,
            aws_region=args.aws_region,
            aws_profile=args.aws_profile,
        )

    LOGGER.info(
        "alpaca stream capture complete",
        extra={
            "stream_url": config.stream_url,
            "raw_messages_path": str(paths.raw_messages_path),
            "canonical_events_path": str(paths.canonical_events_path),
            "captured_messages": len(capture_result.raw_messages),
            "normalized_trade_events": len(capture_result.events),
            "published_to_kinesis": published,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
