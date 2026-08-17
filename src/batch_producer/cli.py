from __future__ import annotations

import argparse
import logging
from pathlib import Path

import boto3

from src.batch_producer.discovery import discover_batch_files
from src.batch_producer.service import BatchIngestionService
from src.common.logging_utils import configure_logging
from src.common.storage import S3DataLakePaths
from src.validation.gx_runner import load_dataframe_from_file, validate_pandas_dataframe

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upload validated financial batch files to S3 Bronze."
    )
    parser.add_argument("--bucket", required=True, help="Target S3 data lake bucket.")
    parser.add_argument("--file", required=False, help="Local batch file path.")
    parser.add_argument(
        "--input-dir",
        required=False,
        help="Directory containing canonical batch files to upload.",
    )
    parser.add_argument(
        "--latest-only",
        action="store_true",
        help="When using --input-dir, upload only the latest file per dataset.",
    )
    parser.add_argument("--aws-profile", required=False, default=None, help="AWS profile name.")
    parser.add_argument("--aws-region", required=True, help="AWS region for the S3 client.")
    parser.add_argument(
        "--batch-raw-prefix",
        default="batch/raw",
        help="S3 prefix for batch Bronze.",
    )
    parser.add_argument(
        "--batch-rejected-prefix",
        default="batch/rejected",
        help="S3 prefix for batch rejected records.",
    )
    parser.add_argument("--batch-silver-prefix", default="batch/silver")
    parser.add_argument("--batch-gold-prefix", default="batch/gold")
    parser.add_argument("--streaming-raw-prefix", default="streaming/raw")
    parser.add_argument("--streaming-rejected-prefix", default="streaming/rejected")
    parser.add_argument("--streaming-silver-prefix", default="streaming/silver")
    parser.add_argument("--streaming-gold-prefix", default="streaming/gold")
    parser.add_argument("--streaming-checkpoint-prefix", default="streaming/checkpoints")
    parser.add_argument("--ge-root", default="great_expectations")
    parser.add_argument("--validation-results-root", default="great_expectations/results")
    parser.add_argument("--run-ge-validation", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.log_level)
    if not args.file and not args.input_dir:
        parser.error("one of --file or --input-dir is required")
    if args.file and args.input_dir:
        parser.error("use either --file or --input-dir, not both")

    session_kwargs: dict[str, str] = {"region_name": args.aws_region}
    if args.aws_profile:
        session_kwargs["profile_name"] = args.aws_profile
    session = boto3.Session(**session_kwargs)

    paths = S3DataLakePaths(
        bucket=args.bucket,
        batch_raw_prefix=args.batch_raw_prefix,
        batch_rejected_prefix=args.batch_rejected_prefix,
        batch_silver_prefix=args.batch_silver_prefix,
        batch_gold_prefix=args.batch_gold_prefix,
        streaming_raw_prefix=args.streaming_raw_prefix,
        streaming_rejected_prefix=args.streaming_rejected_prefix,
        streaming_silver_prefix=args.streaming_silver_prefix,
        streaming_gold_prefix=args.streaming_gold_prefix,
        streaming_checkpoint_prefix=args.streaming_checkpoint_prefix,
    )
    service = BatchIngestionService(session.client("s3"), paths)
    source_files = (
        [Path(args.file)]
        if args.file
        else discover_batch_files(args.input_dir, latest_only=args.latest_only)
    )
    if not source_files:
        raise ValueError("no valid batch files found for upload")

    results = []
    for source_file in source_files:
        result = service.ingest_file(source_file)
        results.append(result)
        if args.run_ge_validation:
            dataset_name = result.dataset_name
            suite_name = {
                "transactions": "transactions_bronze",
                "payments": "payments_bronze",
                "trades": "trades_bronze",
            }.get(dataset_name)
            if suite_name is not None:
                summary = validate_pandas_dataframe(
                    ge_root=args.ge_root,
                    suite_name=suite_name,
                    dataframe=load_dataframe_from_file(source_file),
                    datasource_name="financial_batch_datasource",
                    asset_name=f"{dataset_name}_bronze_asset",
                    batch_definition_name=f"{dataset_name}_bronze_batch",
                    stage="bronze_post_ingest",
                    dataset_name=dataset_name,
                    result_output_dir=args.validation_results_root,
                )
                LOGGER.info(
                    "great expectations validation complete",
                    extra={"suite_name": summary.suite_name, "success": summary.success},
                )
        LOGGER.info(
            "batch ingestion completed",
            extra={
                "bucket": result.bucket,
                "object_key": result.object_key,
                "metadata_key": result.metadata_key,
                "dataset_name": result.dataset_name,
                "row_count": result.row_count,
                "checksum": result.checksum,
            },
        )
    LOGGER.info(
        "batch ingestion summary",
        extra={
            "uploaded_files": len(results),
            "datasets": [result.dataset_name for result in results],
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
