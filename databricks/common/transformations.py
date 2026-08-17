from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as spark_functions

from src.common.constants import (
    VALID_CURRENCY_CODES,
    VALID_PAYMENT_STATUSES,
    VALID_TRANSACTION_TYPES,
)


def add_ingestion_metadata(frame: DataFrame, source_file: str) -> DataFrame:
    return (
        frame.withColumn("source_file", spark_functions.lit(source_file))
        .withColumn("ingestion_timestamp", spark_functions.current_timestamp())
        .withColumn("processing_date", spark_functions.to_date(spark_functions.current_timestamp()))
    )


def standardize_decimal_column(frame: DataFrame, column_name: str) -> DataFrame:
    return frame.withColumn(column_name, spark_functions.col(column_name).cast("decimal(18,2)"))


def split_valid_and_rejected(
    frame: DataFrame,
    id_column: str,
    amount_column: str,
    status_column: str,
    valid_statuses: set[str],
    extra_condition: spark_functions.Column | None = None,
) -> tuple[DataFrame, DataFrame]:
    condition = (
        spark_functions.col(id_column).isNotNull()
        & spark_functions.col("currency_code").isin(sorted(VALID_CURRENCY_CODES))
        & (spark_functions.col(amount_column) >= spark_functions.lit(0))
        & spark_functions.col(status_column).isin(sorted(valid_statuses))
        & spark_functions.col("risk_score").between(0, 100)
    )
    if extra_condition is not None:
        condition = condition & extra_condition
    valid = frame.filter(condition)
    rejected = frame.filter(~condition).withColumn(
        "rejection_reason",
        spark_functions.when(
            spark_functions.col(id_column).isNull(),
            spark_functions.lit(f"{id_column}_null"),
        )
        .when(
            ~spark_functions.col("currency_code").isin(sorted(VALID_CURRENCY_CODES)),
            spark_functions.lit("invalid_currency"),
        )
        .when(spark_functions.col(amount_column) < 0, spark_functions.lit("negative_amount"))
        .when(
            ~spark_functions.col(status_column).isin(sorted(valid_statuses)),
            spark_functions.lit("invalid_status"),
        )
        .otherwise(spark_functions.lit("validation_failed")),
    )
    return valid, rejected


def deduplicate_latest(frame: DataFrame, key_column: str, timestamp_column: str) -> DataFrame:
    window = spark_functions.window
    del window
    ranking_window = (
        __import__("pyspark.sql.window", fromlist=["Window"]).Window.partitionBy(key_column)
        .orderBy(spark_functions.col(timestamp_column).desc())
    )
    return (
        frame.withColumn("_row_number", spark_functions.row_number().over(ranking_window))
        .filter(spark_functions.col("_row_number") == 1)
        .drop("_row_number")
    )


def build_fact_transaction(frame: DataFrame) -> DataFrame:
    return frame.select(
        "transaction_id",
        "account_id",
        "customer_id",
        "transaction_type",
        "transaction_amount",
        "currency_code",
        "transaction_status",
        "event_timestamp",
        "processing_timestamp",
        "merchant_category",
        "country_code",
        "risk_score",
        "ingestion_timestamp",
        "source_file",
        "processing_date",
    )


def build_fact_payment(frame: DataFrame) -> DataFrame:
    return frame.select(
        "payment_id",
        "account_id",
        "customer_id",
        "transaction_amount",
        "currency_code",
        "transaction_status",
        "event_timestamp",
        "processing_timestamp",
        "counterparty_account_id",
        "country_code",
        "risk_score",
        "ingestion_timestamp",
        "source_file",
        "processing_date",
    )


def build_fact_trade(frame: DataFrame) -> DataFrame:
    return frame.select(
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
        "ingestion_timestamp",
        "source_file",
        "processing_date",
    )


def build_fact_daily_account_balance(frame: DataFrame) -> DataFrame:
    return frame.select(
        "balance_id",
        "account_id",
        "customer_id",
        "balance_date",
        "opening_balance",
        "closing_balance",
        "currency_code",
        "ingestion_timestamp",
        "source_file",
        "processing_date",
    )


def build_dim_customer(customers: DataFrame) -> DataFrame:
    return customers.select(
        "customer_id",
        "full_name",
        "email",
        "country_code",
        "risk_score",
        "created_at",
        "ingestion_timestamp",
        "source_file",
        "processing_date",
    )


def build_dim_account(accounts: DataFrame) -> DataFrame:
    return accounts.select(
        "account_id",
        "customer_id",
        "account_type",
        "currency_code",
        "current_balance",
        "opened_at",
        "status",
        "ingestion_timestamp",
        "source_file",
        "processing_date",
    )


def build_dim_security(securities: DataFrame) -> DataFrame:
    return securities.select(
        "security_id",
        "ticker",
        "security_name",
        "security_type",
        "exchange_code",
        "currency_code",
        "ingestion_timestamp",
        "source_file",
        "processing_date",
    )


def transaction_extra_condition() -> spark_functions.Column:
    return spark_functions.col("transaction_type").isin(sorted(VALID_TRANSACTION_TYPES))


def payment_extra_condition() -> spark_functions.Column:
    return spark_functions.col("transaction_status").isin(sorted(VALID_PAYMENT_STATUSES))


def trade_extra_condition() -> spark_functions.Column:
    return spark_functions.col("side").isin(["BUY", "SELL"])
