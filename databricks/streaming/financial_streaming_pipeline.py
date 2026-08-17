from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from databricks.common.streaming_transformations import (
    add_stream_metadata,
    project_payments,
    project_trades,
    project_transactions,
    split_stream_valid_and_rejected,
)
from src.validation.gx_runner import validate_spark_dataframe

LOGGER = logging.getLogger(__name__)

STREAM_EVENT_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("partition_key", StringType(), True),
        StructField("transaction_id", StringType(), True),
        StructField("payment_id", StringType(), True),
        StructField("trade_id", StringType(), True),
        StructField("account_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("security_id", StringType(), True),
        StructField("transaction_type", StringType(), True),
        StructField("transaction_amount", StringType(), True),
        StructField("currency_code", StringType(), True),
        StructField("transaction_status", StringType(), True),
        StructField("event_timestamp", TimestampType(), True),
        StructField("processing_timestamp", TimestampType(), True),
        StructField("merchant_category", StringType(), True),
        StructField("country_code", StringType(), True),
        StructField("risk_score", IntegerType(), True),
        StructField("counterparty_account_id", StringType(), True),
        StructField("quantity", StringType(), True),
        StructField("price", StringType(), True),
        StructField("side", StringType(), True),
        StructField("duplicate_flag", BooleanType(), True),
        StructField("late_arrival_flag", BooleanType(), True),
    ]
)


@dataclass(frozen=True)
class StreamingPaths:
    silver_root: str
    gold_root: str
    rejected_root: str
    checkpoint_root: str

    def silver_path(self, dataset_name: str) -> str:
        return f"{self.silver_root.rstrip('/')}/{dataset_name}"

    def gold_path(self, dataset_name: str) -> str:
        return f"{self.gold_root.rstrip('/')}/{dataset_name}"

    def rejected_path(self, dataset_name: str) -> str:
        return f"{self.rejected_root.rstrip('/')}/{dataset_name}"

    def checkpoint_path(self, dataset_name: str) -> str:
        return f"{self.checkpoint_root.rstrip('/')}/{dataset_name}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Structured Streaming financial data pipeline.")
    parser.add_argument("--stream-name", required=True)
    parser.add_argument("--aws-region", required=True)
    parser.add_argument("--silver-root", required=True)
    parser.add_argument("--gold-root", required=True)
    parser.add_argument("--rejected-root", required=True)
    parser.add_argument("--checkpoint-root", required=True)
    parser.add_argument("--starting-position", default="LATEST")
    parser.add_argument("--trigger-processing-time", default="30 seconds")
    parser.add_argument("--available-now", action="store_true")
    parser.add_argument("--ge-root", default="great_expectations")
    parser.add_argument("--validation-results-root", default="great_expectations/results")
    parser.add_argument("--disable-ge-validation", action="store_true")
    return parser


def parse_kinesis_payload(frame: DataFrame) -> DataFrame:
    return (
        frame.select(
            F.col("partitionKey").alias("partition_key"),
            F.col("sequenceNumber").alias("sequence_number"),
            F.col("approximateArrivalTimestamp").alias("arrival_timestamp"),
            F.col("data").cast("string").alias("raw_data"),
        )
        .withColumn("json_payload", F.from_json(F.col("raw_data"), STREAM_EVENT_SCHEMA))
        .withColumn("parse_failed", F.col("json_payload").isNull())
        .select("partition_key", "sequence_number", "arrival_timestamp", "raw_data", "parse_failed", "json_payload.*")
    )


def prepare_stream(frame: DataFrame) -> DataFrame:
    parsed = parse_kinesis_payload(frame)
    good_records = parsed.filter(~F.col("parse_failed"))
    good_records = (
        add_stream_metadata(good_records)
        .withWatermark("event_timestamp", "10 minutes")
        .dropDuplicates(["event_id"])
    )
    return good_records


def write_stream(frame: DataFrame, target_path: str, checkpoint_path: str, trigger_processing_time: str, available_now: bool) -> None:
    writer = (
        frame.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .partitionBy("processing_date")
    )
    if available_now:
        query = writer.trigger(availableNow=True).start(target_path)
    else:
        query = writer.trigger(processingTime=trigger_processing_time).start(target_path)
    query.awaitTermination()


def foreach_batch_processor(
    paths: StreamingPaths,
    trigger_processing_time: str,
    available_now: bool,
    ge_root: str,
    validation_results_root: str,
    ge_enabled: bool,
):
    del trigger_processing_time, available_now

    def _process(batch_df: DataFrame, batch_id: int) -> None:
        if batch_df.isEmpty():
            LOGGER.info("skipping empty micro-batch", extra={"batch_id": batch_id})
            return
        if ge_enabled:
            validate_spark_dataframe(
                ge_root=ge_root,
                suite_name="streaming_events_microbatch",
                dataframe=batch_df,
                datasource_name="financial_databricks_streaming",
                asset_name="streaming_microbatch_asset",
                batch_definition_name="streaming_microbatch_batch",
                stage="stream_microbatch",
                dataset_name="streaming_events",
                result_output_dir=validation_results_root,
            )
        valid, rejected = split_stream_valid_and_rejected(batch_df)
        transaction_rows = project_transactions(valid)
        payment_rows = project_payments(valid)
        trade_rows = project_trades(valid)

        rejected.write.format("delta").mode("append").partitionBy("processing_date").save(
            paths.rejected_path("events")
        )
        transaction_rows.write.format("delta").mode("append").partitionBy("processing_date").save(
            paths.silver_path("transactions")
        )
        payment_rows.write.format("delta").mode("append").partitionBy("processing_date").save(
            paths.silver_path("payments")
        )
        trade_rows.write.format("delta").mode("append").partitionBy("processing_date").save(
            paths.silver_path("trades")
        )

        transaction_rows.write.format("delta").mode("append").partitionBy("processing_date").save(
            paths.gold_path("fact_transaction")
        )
        payment_rows.write.format("delta").mode("append").partitionBy("processing_date").save(
            paths.gold_path("fact_payment")
        )
        trade_rows.write.format("delta").mode("append").partitionBy("processing_date").save(
            paths.gold_path("fact_trade")
        )

        LOGGER.info(
            "processed micro-batch",
            extra={
                "batch_id": batch_id,
                "input_rows": batch_df.count(),
                "valid_rows": valid.count(),
                "rejected_rows": rejected.count(),
                "transaction_rows": transaction_rows.count(),
                "payment_rows": payment_rows.count(),
                "trade_rows": trade_rows.count(),
            },
        )

    return _process


def run_pipeline(args: argparse.Namespace) -> None:
    spark = (
        SparkSession.builder.appName("financial-streaming-pipeline")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    paths = StreamingPaths(
        silver_root=args.silver_root,
        gold_root=args.gold_root,
        rejected_root=args.rejected_root,
        checkpoint_root=args.checkpoint_root,
    )
    source = (
        spark.readStream.format("kinesis")
        .option("streamName", args.stream_name)
        .option("region", args.aws_region)
        .option("initialPosition", args.starting_position)
        .load()
    )
    prepared = prepare_stream(source)
    query = (
        prepared.writeStream.foreachBatch(
            foreach_batch_processor(
                paths,
                args.trigger_processing_time,
                args.available_now,
                args.ge_root,
                args.validation_results_root,
                not args.disable_ge_validation,
            )
        )
        .option("checkpointLocation", paths.checkpoint_path("events"))
    )
    if args.available_now:
        running = query.trigger(availableNow=True).start()
    else:
        running = query.trigger(processingTime=args.trigger_processing_time).start()
    running.awaitTermination()
    spark.stop()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    parser = build_parser()
    args = parser.parse_args()
    run_pipeline(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
