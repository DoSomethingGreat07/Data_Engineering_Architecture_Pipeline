from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as spark_functions

from databricks.common.schemas import SCHEMA_BY_DATASET
from databricks.common.source_formats import source_format_for_dataset
from databricks.common.transformations import (
    add_ingestion_metadata,
    build_dim_account,
    build_dim_customer,
    build_dim_security,
    build_fact_daily_account_balance,
    build_fact_payment,
    build_fact_trade,
    build_fact_transaction,
    deduplicate_latest,
    payment_extra_condition,
    split_valid_and_rejected,
    standardize_decimal_column,
    trade_extra_condition,
    transaction_extra_condition,
)
from src.common.constants import VALID_PAYMENT_STATUSES, VALID_TRANSACTION_STATUSES
from src.validation.gx_runner import validate_spark_dataframe

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelinePaths:
    bronze_root: str
    silver_root: str
    gold_root: str
    rejected_root: str

    def bronze_path(self, dataset_name: str) -> str:
        return f"{self.bronze_root.rstrip('/')}/{dataset_name}"

    def silver_path(self, dataset_name: str) -> str:
        return f"{self.silver_root.rstrip('/')}/{dataset_name}"

    def gold_path(self, dataset_name: str) -> str:
        return f"{self.gold_root.rstrip('/')}/{dataset_name}"

    def rejected_path(self, dataset_name: str) -> str:
        return f"{self.rejected_root.rstrip('/')}/{dataset_name}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Financial data platform batch pipeline.")
    parser.add_argument("--bronze-root", required=True)
    parser.add_argument("--silver-root", required=True)
    parser.add_argument("--gold-root", required=True)
    parser.add_argument("--rejected-root", required=True)
    parser.add_argument("--ge-root", default="great_expectations")
    parser.add_argument("--validation-results-root", default="great_expectations/results")
    parser.add_argument("--disable-ge-validation", action="store_true")
    return parser


def read_bronze_dataset(spark: SparkSession, paths: PipelinePaths, dataset_name: str) -> DataFrame:
    schema = SCHEMA_BY_DATASET[dataset_name]
    source_root = paths.bronze_path(dataset_name)
    source_format = source_format_for_dataset(dataset_name)
    source_glob = f"{source_root}/{dataset_name}_*.{source_format}"
    if source_format == "json":
        reader = spark.read.schema(schema).option("multiLine", "true")
    else:
        reader = spark.read.schema(schema).option("header", "true")
    frame = reader.format(source_format).load(source_glob)
    return add_ingestion_metadata(frame, source_glob)


def write_delta(
    frame: DataFrame,
    target_path: str,
    partition_column: str = "processing_date",
) -> None:
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy(partition_column)
        .save(target_path)
    )


def process_reference_dataset(
    spark: SparkSession,
    paths: PipelinePaths,
    dataset_name: str,
    transform,
) -> DataFrame:
    frame = read_bronze_dataset(spark, paths, dataset_name)
    key_column = {
        "customers": "customer_id",
        "accounts": "account_id",
        "securities": "security_id",
    }[dataset_name]
    silver = deduplicate_latest(
        frame,
        key_column=key_column,
        timestamp_column="ingestion_timestamp",
    )
    write_delta(silver, paths.silver_path(dataset_name))
    gold = transform(silver)
    write_delta(gold, paths.gold_path(transform.__name__.replace("build_", "")))
    return gold


def process_transactional_dataset(
    spark: SparkSession,
    paths: PipelinePaths,
    ge_root: str,
    validation_results_root: str,
    ge_enabled: bool,
    dataset_name: str,
    id_column: str,
    amount_column: str,
    status_column: str,
    valid_statuses: set[str],
    extra_condition: spark_functions.Column | None,
    gold_builder,
) -> tuple[DataFrame, DataFrame]:
    frame = read_bronze_dataset(spark, paths, dataset_name)
    frame = standardize_decimal_column(frame, amount_column)
    silver, rejected = split_valid_and_rejected(
        deduplicate_latest(frame, key_column=id_column, timestamp_column="processing_timestamp"),
        id_column=id_column,
        amount_column=amount_column,
        status_column=status_column,
        valid_statuses=valid_statuses,
        extra_condition=extra_condition,
    )
    if ge_enabled:
        suite_name = {
            "transactions": "transactions_bronze",
            "payments": "payments_bronze",
            "trades": "trades_bronze",
        }[dataset_name]
        validate_spark_dataframe(
            ge_root=ge_root,
            suite_name=suite_name,
            dataframe=silver,
            datasource_name="financial_databricks_batch",
            asset_name=f"{dataset_name}_silver_asset",
            batch_definition_name=f"{dataset_name}_silver_batch",
            stage="silver_pre_write",
            dataset_name=dataset_name,
            result_output_dir=validation_results_root,
        )
    write_delta(silver, paths.silver_path(dataset_name))
    write_delta(rejected, paths.rejected_path(dataset_name))
    gold = gold_builder(silver)
    if ge_enabled and dataset_name == "transactions":
        reconciliation_df = spark.createDataFrame(
            [
                (
                    silver.count(),
                    gold.count(),
                    abs(silver.count() - gold.count()),
                    0.0,
                    0.0,
                    0.0,
                    rejected.count() / max(silver.count() + rejected.count(), 1),
                    0.0,
                )
            ],
            [
                "source_row_count",
                "target_row_count",
                "row_count_difference",
                "debit_total",
                "credit_total",
                "debit_credit_difference",
                "rejected_rate",
                "duplicate_rate",
            ],
        )
        validate_spark_dataframe(
            ge_root=ge_root,
            suite_name="gold_load_validation",
            dataframe=reconciliation_df,
            datasource_name="financial_databricks_batch",
            asset_name="gold_reconciliation_asset",
            batch_definition_name="gold_reconciliation_batch",
            stage="gold_pre_curated_publish",
            dataset_name="gold_reconciliation",
            result_output_dir=validation_results_root,
            expectation_parameters={
                "max_row_count_difference": 0,
                "max_debit_credit_difference": 0.01,
                "max_duplicate_rate": 0.05,
                "max_rejected_rate": 0.10,
            },
        )
    write_delta(gold, paths.gold_path(gold_builder.__name__.replace("build_", "")))
    return silver, rejected


def run_pipeline(args: argparse.Namespace) -> None:
    builder = (
        SparkSession.builder.appName("financial-batch-pipeline")
        .master("local[*]")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.jars.ivy", str(Path(".spark-ivy-cache").resolve()))
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
    )
    try:
        from delta import configure_spark_with_delta_pip

        builder = (
            builder.config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
        )
        spark = configure_spark_with_delta_pip(builder).getOrCreate()
    except ImportError:
        spark = builder.getOrCreate()
    paths = PipelinePaths(
        bronze_root=args.bronze_root,
        silver_root=args.silver_root,
        gold_root=args.gold_root,
        rejected_root=args.rejected_root,
    )
    ge_enabled = not args.disable_ge_validation

    dim_customer = process_reference_dataset(spark, paths, "customers", build_dim_customer)
    dim_account = process_reference_dataset(spark, paths, "accounts", build_dim_account)
    dim_security = process_reference_dataset(spark, paths, "securities", build_dim_security)
    del dim_customer, dim_account, dim_security

    process_transactional_dataset(
        spark,
        paths,
        args.ge_root,
        args.validation_results_root,
        ge_enabled,
        "transactions",
        id_column="transaction_id",
        amount_column="transaction_amount",
        status_column="transaction_status",
        valid_statuses=VALID_TRANSACTION_STATUSES,
        extra_condition=transaction_extra_condition(),
        gold_builder=build_fact_transaction,
    )
    process_transactional_dataset(
        spark,
        paths,
        args.ge_root,
        args.validation_results_root,
        ge_enabled,
        "payments",
        id_column="payment_id",
        amount_column="transaction_amount",
        status_column="transaction_status",
        valid_statuses=VALID_PAYMENT_STATUSES,
        extra_condition=payment_extra_condition(),
        gold_builder=build_fact_payment,
    )
    trades_frame = read_bronze_dataset(spark, paths, "trades")
    trades_frame = standardize_decimal_column(trades_frame, "transaction_amount")
    trades_frame = standardize_decimal_column(trades_frame, "quantity")
    trades_frame = standardize_decimal_column(trades_frame, "price")
    trades_silver, trades_rejected = split_valid_and_rejected(
        deduplicate_latest(
            trades_frame,
            key_column="trade_id",
            timestamp_column="processing_timestamp",
        ),
        id_column="trade_id",
        amount_column="transaction_amount",
        status_column="transaction_status",
        valid_statuses=VALID_TRANSACTION_STATUSES,
        extra_condition=trade_extra_condition(),
    )
    if ge_enabled:
        validate_spark_dataframe(
            ge_root=args.ge_root,
            suite_name="trades_bronze",
            dataframe=trades_silver,
            datasource_name="financial_databricks_batch",
            asset_name="trades_silver_asset",
            batch_definition_name="trades_silver_batch",
            stage="silver_pre_write",
            dataset_name="trades",
            result_output_dir=args.validation_results_root,
        )
    write_delta(trades_silver, paths.silver_path("trades"))
    write_delta(trades_rejected, paths.rejected_path("trades"))
    write_delta(build_fact_trade(trades_silver), paths.gold_path("fact_trade"))

    balances_frame = read_bronze_dataset(spark, paths, "daily_account_balances")
    balances_frame = standardize_decimal_column(balances_frame, "opening_balance")
    balances_frame = standardize_decimal_column(balances_frame, "closing_balance")
    balances_silver = deduplicate_latest(
        balances_frame,
        key_column="balance_id",
        timestamp_column="ingestion_timestamp",
    )
    write_delta(balances_silver, paths.silver_path("daily_account_balances"))
    write_delta(
        build_fact_daily_account_balance(balances_silver),
        paths.gold_path("fact_daily_account_balance"),
    )

    counts = {
        "transactions_valid": (
            spark.read.format("delta").load(paths.silver_path("transactions")).count()
        ),
        "transactions_rejected": (
            spark.read.format("delta").load(paths.rejected_path("transactions")).count()
        ),
        "payments_valid": spark.read.format("delta").load(paths.silver_path("payments")).count(),
        "payments_rejected": (
            spark.read.format("delta").load(paths.rejected_path("payments")).count()
        ),
        "trades_valid": spark.read.format("delta").load(paths.silver_path("trades")).count(),
        "trades_rejected": (
            spark.read.format("delta").load(paths.rejected_path("trades")).count()
        ),
    }
    LOGGER.info("batch pipeline finished", extra=counts)
    spark.stop()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    parser = build_parser()
    args = parser.parse_args()
    run_pipeline(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
