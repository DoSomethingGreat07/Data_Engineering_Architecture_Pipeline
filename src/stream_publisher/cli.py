from __future__ import annotations

import argparse
import json
from pathlib import Path

import boto3

from src.batch_publisher.s3_sync import publish_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish realtime streaming raw/silver/gold/rejected outputs to S3."
    )
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--raw-local-root", default="data/lakehouse/streaming/raw")
    parser.add_argument("--silver-local-root", default="data/lakehouse/streaming/silver")
    parser.add_argument("--gold-local-root", default="data/lakehouse/streaming/gold")
    parser.add_argument("--rejected-local-root", default="data/lakehouse/streaming/rejected")
    parser.add_argument("--raw-prefix", default="streaming/raw")
    parser.add_argument("--silver-prefix", default="streaming/silver")
    parser.add_argument("--gold-prefix", default="streaming/gold")
    parser.add_argument("--rejected-prefix", default="streaming/rejected")
    parser.add_argument("--aws-region", default=None)
    parser.add_argument("--aws-profile", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    session_kwargs = {}
    if args.aws_region:
        session_kwargs["region_name"] = args.aws_region
    if args.aws_profile:
        session_kwargs["profile_name"] = args.aws_profile

    session = boto3.Session(**session_kwargs)
    s3_client = session.client("s3")
    published = {
        "raw": publish_directory(
            s3_client=s3_client,
            bucket=args.bucket,
            local_root=Path(args.raw_local_root),
            s3_prefix=args.raw_prefix,
        ),
        "silver": publish_directory(
            s3_client=s3_client,
            bucket=args.bucket,
            local_root=Path(args.silver_local_root),
            s3_prefix=args.silver_prefix,
        ),
        "gold": publish_directory(
            s3_client=s3_client,
            bucket=args.bucket,
            local_root=Path(args.gold_local_root),
            s3_prefix=args.gold_prefix,
        ),
        "rejected": publish_directory(
            s3_client=s3_client,
            bucket=args.bucket,
            local_root=Path(args.rejected_local_root),
            s3_prefix=args.rejected_prefix,
        ),
    }
    print(
        json.dumps(
            {
                layer: [
                    {"local_path": str(item.local_path), "s3_key": item.s3_key}
                    for item in items
                ]
                for layer, items in published.items()
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

