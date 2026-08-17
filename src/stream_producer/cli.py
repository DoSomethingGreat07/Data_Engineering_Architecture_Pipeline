from __future__ import annotations

import argparse
import logging

import boto3

from src.common.logging_utils import configure_logging
from src.stream_producer.models import ProducerSettings
from src.stream_producer.service import KinesisProducerService, load_stream_events

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish synthetic financial events to Amazon Kinesis."
    )
    parser.add_argument("--stream-name", required=True, help="Kinesis stream name.")
    parser.add_argument("--events-file", required=True, help="Path to generated events JSONL file.")
    parser.add_argument("--aws-region", required=True, help="AWS region.")
    parser.add_argument("--aws-profile", default=None, help="Optional AWS profile.")
    parser.add_argument(
        "--events-per-second",
        type=int,
        default=5,
        help="Target event publish rate.",
    )
    parser.add_argument(
        "--finite-event-count",
        type=int,
        default=None,
        help="Optional max event count for finite test runs.",
    )
    parser.add_argument(
        "--no-sleep",
        action="store_true",
        help="Disable rate-limit sleeping for local tests.",
    )
    parser.add_argument("--log-level", default="INFO")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.log_level)

    session_kwargs: dict[str, str] = {"region_name": args.aws_region}
    if args.aws_profile:
        session_kwargs["profile_name"] = args.aws_profile
    session = boto3.Session(**session_kwargs)

    events = load_stream_events(args.events_file)
    service = KinesisProducerService(
        session.client("kinesis"),
        ProducerSettings(
            stream_name=args.stream_name,
            events_per_second=args.events_per_second,
            finite_event_count=args.finite_event_count,
            sleep_enabled=not args.no_sleep,
        ),
    )
    result = service.send_events(events)
    LOGGER.info(
        "stream publishing complete",
        extra={
            "attempted_records": result.attempted_records,
            "successful_records": result.successful_records,
            "failed_records": result.failed_records,
            "started_at": result.started_at.isoformat(),
            "finished_at": result.finished_at.isoformat(),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

