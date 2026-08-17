from __future__ import annotations

import argparse
import json

import boto3
from botocore.exceptions import ClientError

PARQUET_INPUT_FORMAT = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
PARQUET_OUTPUT_FORMAT = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
PARQUET_SERDE = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Register isolated realtime streaming tables in AWS Glue."
    )
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--database-name", default="fdp_dev_streaming_lakehouse")
    parser.add_argument("--aws-region", required=True)
    parser.add_argument("--aws-profile", default=None)
    parser.add_argument("--silver-prefix", default="streaming/silver")
    parser.add_argument("--gold-prefix", default="streaming/gold")
    parser.add_argument("--rejected-prefix", default="streaming/rejected")
    return parser


def table_definitions(
    bucket: str,
    silver_prefix: str,
    gold_prefix: str,
    rejected_prefix: str,
) -> dict[str, dict[str, object]]:
    return {
        "silver_trades": {
            "location": f"s3://{bucket}/{silver_prefix.strip('/')}/trades/",
            "columns": [
                {"Name": "event_id", "Type": "string"},
                {"Name": "trade_id", "Type": "string"},
                {"Name": "account_id", "Type": "string"},
                {"Name": "customer_id", "Type": "string"},
                {"Name": "security_id", "Type": "string"},
                {"Name": "quantity", "Type": "decimal(18,2)"},
                {"Name": "price", "Type": "decimal(18,2)"},
                {"Name": "transaction_amount", "Type": "decimal(18,2)"},
                {"Name": "currency_code", "Type": "string"},
                {"Name": "side", "Type": "string"},
                {"Name": "transaction_status", "Type": "string"},
                {"Name": "event_timestamp", "Type": "timestamp"},
                {"Name": "processing_timestamp", "Type": "timestamp"},
                {"Name": "country_code", "Type": "string"},
                {"Name": "risk_score", "Type": "int"},
                {"Name": "ingestion_timestamp", "Type": "timestamp"},
            ],
        },
        "rejected_stream_events": {
            "location": f"s3://{bucket}/{rejected_prefix.strip('/')}/events/",
            "columns": [
                {"Name": "event_id", "Type": "string"},
                {"Name": "event_type", "Type": "string"},
                {"Name": "partition_key", "Type": "string"},
                {"Name": "trade_id", "Type": "string"},
                {"Name": "account_id", "Type": "string"},
                {"Name": "customer_id", "Type": "string"},
                {"Name": "security_id", "Type": "string"},
                {"Name": "transaction_amount", "Type": "decimal(18,2)"},
                {"Name": "currency_code", "Type": "string"},
                {"Name": "transaction_status", "Type": "string"},
                {"Name": "event_timestamp", "Type": "timestamp"},
                {"Name": "processing_timestamp", "Type": "timestamp"},
                {"Name": "country_code", "Type": "string"},
                {"Name": "risk_score", "Type": "int"},
                {"Name": "duplicate_flag", "Type": "boolean"},
                {"Name": "late_arrival_flag", "Type": "boolean"},
                {"Name": "raw_payload", "Type": "string"},
                {"Name": "ingestion_timestamp", "Type": "timestamp"},
                {"Name": "rejection_reason", "Type": "string"},
            ],
        },
        "gold_fact_trade": {
            "location": f"s3://{bucket}/{gold_prefix.strip('/')}/fact_trade/",
            "columns": [
                {"Name": "event_id", "Type": "string"},
                {"Name": "trade_id", "Type": "string"},
                {"Name": "account_id", "Type": "string"},
                {"Name": "customer_id", "Type": "string"},
                {"Name": "security_id", "Type": "string"},
                {"Name": "quantity", "Type": "decimal(18,2)"},
                {"Name": "price", "Type": "decimal(18,2)"},
                {"Name": "transaction_amount", "Type": "decimal(18,2)"},
                {"Name": "currency_code", "Type": "string"},
                {"Name": "side", "Type": "string"},
                {"Name": "transaction_status", "Type": "string"},
                {"Name": "event_timestamp", "Type": "timestamp"},
                {"Name": "processing_timestamp", "Type": "timestamp"},
                {"Name": "country_code", "Type": "string"},
                {"Name": "risk_score", "Type": "int"},
                {"Name": "ingestion_timestamp", "Type": "timestamp"},
            ],
        },
        "gold_trade_minute_metrics": {
            "location": f"s3://{bucket}/{gold_prefix.strip('/')}/trade_minute_metrics/",
            "columns": [
                {"Name": "security_id", "Type": "string"},
                {"Name": "currency_code", "Type": "string"},
                {"Name": "side", "Type": "string"},
                {"Name": "trade_minute", "Type": "timestamp"},
                {"Name": "trade_count", "Type": "bigint"},
                {"Name": "total_quantity", "Type": "decimal(18,2)"},
                {"Name": "total_transaction_amount", "Type": "decimal(18,2)"},
                {"Name": "avg_trade_price", "Type": "decimal(18,2)"},
                {"Name": "max_risk_score", "Type": "int"},
            ],
        },
        "gold_customer_trade_exposure": {
            "location": f"s3://{bucket}/{gold_prefix.strip('/')}/customer_trade_exposure/",
            "columns": [
                {"Name": "customer_id", "Type": "string"},
                {"Name": "account_id", "Type": "string"},
                {"Name": "security_id", "Type": "string"},
                {"Name": "currency_code", "Type": "string"},
                {"Name": "buy_trade_count", "Type": "bigint"},
                {"Name": "sell_trade_count", "Type": "bigint"},
                {"Name": "net_quantity", "Type": "decimal(18,2)"},
                {"Name": "gross_notional_amount", "Type": "decimal(18,2)"},
                {"Name": "avg_risk_score", "Type": "double"},
                {"Name": "latest_event_timestamp", "Type": "timestamp"},
            ],
        },
    }


def build_table_input(table_name: str, definition: dict[str, object]) -> dict[str, object]:
    location = str(definition["location"])
    return {
        "Name": table_name,
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {"classification": "parquet", "EXTERNAL": "TRUE"},
        "StorageDescriptor": {
            "Columns": definition["columns"],
            "Location": location,
            "InputFormat": PARQUET_INPUT_FORMAT,
            "OutputFormat": PARQUET_OUTPUT_FORMAT,
            "SerdeInfo": {
                "SerializationLibrary": PARQUET_SERDE,
                "Parameters": {"serialization.format": "1"},
            },
        },
        "PartitionKeys": [{"Name": "processing_date", "Type": "date"}],
    }


def main() -> int:
    args = build_parser().parse_args()
    session_kwargs: dict[str, str] = {"region_name": args.aws_region}
    if args.aws_profile:
        session_kwargs["profile_name"] = args.aws_profile
    session = boto3.Session(**session_kwargs)
    glue = session.client("glue")

    try:
        glue.create_database(
            DatabaseInput={
                "Name": args.database_name,
                "Description": "Isolated Glue catalog for realtime streaming financial analytics.",
            }
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "AlreadyExistsException":
            raise
    created_tables: list[str] = []
    updated_tables: list[str] = []
    table_inputs = table_definitions(
        args.bucket,
        args.silver_prefix,
        args.gold_prefix,
        args.rejected_prefix,
    )

    for table_name, definition in table_inputs.items():
        table_input = build_table_input(table_name, definition)
        try:
            glue.create_table(DatabaseName=args.database_name, TableInput=table_input)
            created_tables.append(table_name)
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "AlreadyExistsException":
                raise
            glue.update_table(DatabaseName=args.database_name, TableInput=table_input)
            updated_tables.append(table_name)

    print(
        json.dumps(
            {
                "database_name": args.database_name,
                "created_tables": created_tables,
                "updated_tables": updated_tables,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
