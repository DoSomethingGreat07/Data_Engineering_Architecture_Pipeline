from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

from src.common.constants import (
    VALID_CURRENCY_CODES,
    VALID_PAYMENT_STATUSES,
    VALID_TRANSACTION_STATUSES,
    VALID_TRANSACTION_TYPES,
)


def ensure_stream_optional_columns(frame: DataFrame) -> DataFrame:
    optional_columns = [
        "transaction_id",
        "transaction_type",
        "payment_id",
        "merchant_category",
        "counterparty_account_id",
    ]
    for column_name in optional_columns:
        if column_name not in frame.columns:
            frame = frame.withColumn(column_name, F.lit(None).cast(StringType()))
    return frame


def add_stream_metadata(frame: DataFrame) -> DataFrame:
    return (
        frame.withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("processing_date", F.to_date(F.current_timestamp()))
        .withColumn("raw_payload", F.to_json(F.struct(*frame.columns)))
    )


def split_stream_valid_and_rejected(frame: DataFrame) -> tuple[DataFrame, DataFrame]:
    frame = ensure_stream_optional_columns(frame)
    transaction_condition = (
        (F.col("event_type") == F.lit("transaction"))
        & F.col("transaction_id").isNotNull()
        & F.col("transaction_type").isin(sorted(VALID_TRANSACTION_TYPES))
        & F.col("transaction_status").isin(sorted(VALID_TRANSACTION_STATUSES))
    )
    payment_condition = (
        (F.col("event_type") == F.lit("payment"))
        & F.col("payment_id").isNotNull()
        & F.col("transaction_status").isin(sorted(VALID_PAYMENT_STATUSES))
    )
    trade_condition = (
        (F.col("event_type") == F.lit("trade"))
        & F.col("trade_id").isNotNull()
        & F.col("side").isin(["BUY", "SELL"])
        & F.col("transaction_status").isin(sorted(VALID_TRANSACTION_STATUSES))
    )
    universal_condition = (
        F.col("currency_code").isin(sorted(VALID_CURRENCY_CODES))
        & F.col("risk_score").between(0, 100)
        & (F.col("transaction_amount").cast("decimal(18,2)") >= 0)
    )
    valid_condition = universal_condition & (
        transaction_condition | payment_condition | trade_condition
    )

    valid = frame.filter(valid_condition)
    rejected = frame.filter(~valid_condition).withColumn(
        "rejection_reason",
        F.when(~F.col("currency_code").isin(sorted(VALID_CURRENCY_CODES)), F.lit("invalid_currency"))
        .when(~F.col("risk_score").between(0, 100), F.lit("invalid_risk_score"))
        .when(F.col("transaction_amount").cast("decimal(18,2)") < 0, F.lit("negative_amount"))
        .when(F.col("event_type") == "transaction", F.lit("invalid_transaction_record"))
        .when(F.col("event_type") == "payment", F.lit("invalid_payment_record"))
        .otherwise(F.lit("invalid_trade_record")),
    )
    return valid, rejected


def project_transactions(frame: DataFrame) -> DataFrame:
    frame = ensure_stream_optional_columns(frame)
    return frame.filter(F.col("event_type") == "transaction").select(
        "event_id",
        "transaction_id",
        "account_id",
        "customer_id",
        "transaction_type",
        F.col("transaction_amount").cast("decimal(18,2)").alias("transaction_amount"),
        "currency_code",
        "transaction_status",
        "event_timestamp",
        "processing_timestamp",
        "merchant_category",
        "country_code",
        "risk_score",
        "ingestion_timestamp",
        "processing_date",
    )


def project_payments(frame: DataFrame) -> DataFrame:
    frame = ensure_stream_optional_columns(frame)
    return frame.filter(F.col("event_type") == "payment").select(
        "event_id",
        "payment_id",
        "account_id",
        "customer_id",
        F.col("transaction_amount").cast("decimal(18,2)").alias("transaction_amount"),
        "currency_code",
        "transaction_status",
        "event_timestamp",
        "processing_timestamp",
        "counterparty_account_id",
        "country_code",
        "risk_score",
        "ingestion_timestamp",
        "processing_date",
    )


def project_trades(frame: DataFrame) -> DataFrame:
    return frame.filter(F.col("event_type") == "trade").select(
        "event_id",
        "trade_id",
        "account_id",
        "customer_id",
        "security_id",
        F.col("quantity").cast("decimal(18,2)").alias("quantity"),
        F.col("price").cast("decimal(18,2)").alias("price"),
        F.col("transaction_amount").cast("decimal(18,2)").alias("transaction_amount"),
        "currency_code",
        "side",
        "transaction_status",
        "event_timestamp",
        "processing_timestamp",
        "country_code",
        "risk_score",
        "ingestion_timestamp",
        "processing_date",
    )
