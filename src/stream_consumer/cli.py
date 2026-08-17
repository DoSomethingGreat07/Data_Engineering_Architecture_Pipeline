from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import boto3

from src.common.logging_utils import configure_logging
from src.stream_consumer.service import ConsumeRequest, KinesisStreamConsumerService

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Consume a realtime micro-batch from Kinesis and persist raw/canonical files."
    )
    parser.add_argument("--stream-name", required=True)
    parser.add_argument("--aws-region", required=True)
    parser.add_argument("--aws-profile", default=None)
    parser.add_argument("--output-dir", default="data/external_sources/streaming")
    parser.add_argument("--bronze-root", default="data/lakehouse/streaming/raw")
    parser.add_argument("--max-records", type=int, default=250)
    parser.add_argument("--iterator-type", default="LATEST")
    parser.add_argument("--poll-interval-seconds", type=float, default=1.0)
    parser.add_argument("--max-empty-polls", type=int, default=3)
    parser.add_argument("--log-level", default="INFO")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.log_level)

    session_kwargs: dict[str, str] = {"region_name": args.aws_region}
    if args.aws_profile:
        session_kwargs["profile_name"] = args.aws_profile
    session = boto3.Session(**session_kwargs)
    service = KinesisStreamConsumerService(session.client("kinesis"))

    result = service.consume_to_directory(
        output_dir=Path(args.output_dir),
        bronze_root=Path(args.bronze_root),
        request=ConsumeRequest(
            stream_name=args.stream_name,
            max_records=args.max_records,
            iterator_type=args.iterator_type,
            poll_interval_seconds=args.poll_interval_seconds,
            max_empty_polls=args.max_empty_polls,
        ),
    )
    LOGGER.info(
        "kinesis micro-batch consumed",
        extra={
            "records_read": result.records_read,
            "parsed_records": result.parsed_records,
            "parse_failures": result.parse_failures,
            "raw_messages_path": str(result.paths.raw_messages_path),
            "canonical_events_path": str(result.paths.canonical_events_path),
            "bronze_events_path": str(result.paths.bronze_events_path),
        },
    )
    print(
        json.dumps(
            {
                "records_read": result.records_read,
                "parsed_records": result.parsed_records,
                "parse_failures": result.parse_failures,
                "raw_messages_path": str(result.paths.raw_messages_path),
                "canonical_events_path": str(result.paths.canonical_events_path),
                "bronze_events_path": str(result.paths.bronze_events_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

