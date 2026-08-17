from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

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
    project_trades,
    split_stream_valid_and_rejected,
)
from src.validation.gx_runner import validate_spark_dataframe

LOGGER = logging.getLogger(__name__)

STREAM_EVENT_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("partition_key", StringType(), True),
        StructField("trade_id", StringType(), True),
        StructField("account_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("security_id", StringType(), True),
        StructField("transaction_amount", StringType(), True),
        StructField("currency_code", StringType(), True),
        StructField("transaction_status", StringType(), True),
        StructField("event_timestamp", TimestampType(), True),
        StructField("processing_timestamp", TimestampType(), True),
        StructField("country_code", StringType(), True),
        StructField("risk_score", IntegerType(), True),
        StructField("quantity", StringType(), True),
        StructField("price", StringType(), True),
        StructField("side", StringType(), True),
        StructField("duplicate_flag", BooleanType(), True),
        StructField("late_arrival_flag", BooleanType(), True),
    ]
)


@dataclass(frozen=True)
class StreamingPaths:
    raw_root: str
    silver_root: str
    gold_root: str
    rejected_root: str

    def raw_path(self, dataset_name: str) -> str:
        return f"{self.raw_root.rstrip('/')}/{dataset_name}"

    def silver_path(self, dataset_name: str) -> str:
        return f"{self.silver_root.rstrip('/')}/{dataset_name}"

    def gold_path(self, dataset_name: str) -> str:
        return f"{self.gold_root.rstrip('/')}/{dataset_name}"

    def rejected_path(self, dataset_name: str) -> str:
        return f"{self.rejected_root.rstrip('/')}/{dataset_name}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Realtime financial streaming micro-batch pipeline.")
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--silver-root", required=True)
    parser.add_argument("--gold-root", required=True)
    parser.add_argument("--rejected-root", required=True)
    parser.add_argument("--ge-root", default="great_expectations")
    parser.add_argument("--validation-results-root", default="great_expectations/results")
    parser.add_argument("--disable-ge-validation", action="store_true")
    return parser


def read_raw_events(spark: SparkSession, paths: StreamingPaths) -> DataFrame:
    source_glob = f"{paths.raw_path('events')}/stream_events_*.jsonl"
    frame = spark.read.schema(STREAM_EVENT_SCHEMA).json(source_glob)
    frame = add_stream_metadata(frame).withColumn("source_file", F.input_file_name())
    ranking_window = (
        __import__("pyspark.sql.window", fromlist=["Window"]).Window.partitionBy("event_id")
        .orderBy(F.col("processing_timestamp").desc())
    )
    return (
        frame.withColumn("_row_number", F.row_number().over(ranking_window))
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
    )


def write_parquet(frame: DataFrame, target_path: str) -> None:
    (
        frame.write.mode("overwrite")
        .format("parquet")
        .option("compression", "snappy")
        .partitionBy("processing_date")
        .save(target_path)
    )


def build_trade_minute_metrics(trades: DataFrame) -> DataFrame:
    return (
        trades.withColumn("trade_minute", F.date_trunc("minute", F.col("event_timestamp")))
        .groupBy("security_id", "currency_code", "side", "trade_minute", "processing_date")
        .agg(
            F.count("*").alias("trade_count"),
            F.sum("quantity").cast("decimal(18,2)").alias("total_quantity"),
            F.sum("transaction_amount").cast("decimal(18,2)").alias("total_transaction_amount"),
            F.avg("price").cast("decimal(18,2)").alias("avg_trade_price"),
            F.max("risk_score").alias("max_risk_score"),
        )
    )


def build_customer_trade_exposure(trades: DataFrame) -> DataFrame:
    return (
        trades.groupBy("customer_id", "account_id", "security_id", "currency_code", "processing_date")
        .agg(
            F.sum(F.when(F.col("side") == "BUY", F.lit(1)).otherwise(F.lit(0))).alias("buy_trade_count"),
            F.sum(F.when(F.col("side") == "SELL", F.lit(1)).otherwise(F.lit(0))).alias("sell_trade_count"),
            F.sum(
                F.when(F.col("side") == "BUY", F.col("quantity")).otherwise(-F.col("quantity"))
            ).cast("decimal(18,2)").alias("net_quantity"),
            F.sum("transaction_amount").cast("decimal(18,2)").alias("gross_notional_amount"),
            F.avg("risk_score").alias("avg_risk_score"),
            F.max("event_timestamp").alias("latest_event_timestamp"),
        )
    )


def run_pipeline(args: argparse.Namespace) -> None:
    builder = (
        SparkSession.builder.appName("financial-streaming-microbatch-pipeline")
        .master("local[*]")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.jars.ivy", str(Path(".spark-ivy-cache").resolve()))
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
    )
    spark = builder.getOrCreate()
    paths = StreamingPaths(
        raw_root=args.raw_root,
        silver_root=args.silver_root,
        gold_root=args.gold_root,
        rejected_root=args.rejected_root,
    )
    ge_enabled = not args.disable_ge_validation

    events = read_raw_events(spark, paths)
    valid_events, rejected_events = split_stream_valid_and_rejected(events)
    trades = project_trades(valid_events)

    if ge_enabled:
        validate_spark_dataframe(
            ge_root=args.ge_root,
            suite_name="streaming_events_microbatch",
            dataframe=valid_events.select(
                "event_id",
                "event_type",
                "partition_key",
                "event_timestamp",
                "processing_timestamp",
                "currency_code",
                "transaction_status",
                "transaction_amount",
                "risk_score",
            ),
            datasource_name="financial_streaming_microbatch",
            asset_name="streaming_events_valid_asset",
            batch_definition_name="streaming_events_valid_batch",
            stage="stream_microbatch",
            dataset_name="streaming_events",
            result_output_dir=args.validation_results_root,
        )
        validate_spark_dataframe(
            ge_root=args.ge_root,
            suite_name="trades_bronze",
            dataframe=trades.select(
                "trade_id",
                "account_id",
                "customer_id",
                "security_id",
                "quantity",
                "price",
                "transaction_amount",
                "currency_code",
                "side",
                "transaction_status",
                "event_timestamp",
                "processing_timestamp",
                "country_code",
                "risk_score",
            ),
            datasource_name="financial_streaming_microbatch",
            asset_name="streaming_trades_silver_asset",
            batch_definition_name="streaming_trades_silver_batch",
            stage="stream_silver",
            dataset_name="trades",
            result_output_dir=args.validation_results_root,
        )

    write_parquet(rejected_events, paths.rejected_path("events"))
    write_parquet(trades, paths.silver_path("trades"))
    write_parquet(trades, paths.gold_path("fact_trade"))
    write_parquet(build_trade_minute_metrics(trades), paths.gold_path("trade_minute_metrics"))
    write_parquet(build_customer_trade_exposure(trades), paths.gold_path("customer_trade_exposure"))

    LOGGER.info(
        "streaming micro-batch pipeline finished",
        extra={
            "input_rows": events.count(),
            "valid_rows": valid_events.count(),
            "rejected_rows": rejected_events.count(),
            "trade_rows": trades.count(),
        },
    )
    spark.stop()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = build_parser().parse_args()
    run_pipeline(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

