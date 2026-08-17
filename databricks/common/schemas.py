from __future__ import annotations

from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

CUSTOMER_SCHEMA = StructType(
    [
        StructField("customer_id", StringType(), False),
        StructField("full_name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("country_code", StringType(), True),
        StructField("risk_score", IntegerType(), True),
        StructField("created_at", TimestampType(), True),
    ]
)

ACCOUNT_SCHEMA = StructType(
    [
        StructField("account_id", StringType(), False),
        StructField("customer_id", StringType(), False),
        StructField("account_type", StringType(), True),
        StructField("currency_code", StringType(), True),
        StructField("current_balance", StringType(), True),
        StructField("opened_at", TimestampType(), True),
        StructField("status", StringType(), True),
    ]
)

SECURITY_SCHEMA = StructType(
    [
        StructField("security_id", StringType(), False),
        StructField("ticker", StringType(), True),
        StructField("security_name", StringType(), True),
        StructField("security_type", StringType(), True),
        StructField("exchange_code", StringType(), True),
        StructField("currency_code", StringType(), True),
    ]
)

TRANSACTION_SCHEMA = StructType(
    [
        StructField("transaction_id", StringType(), True),
        StructField("account_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("transaction_type", StringType(), True),
        StructField("transaction_amount", StringType(), True),
        StructField("currency_code", StringType(), True),
        StructField("transaction_status", StringType(), True),
        StructField("event_timestamp", TimestampType(), True),
        StructField("processing_timestamp", TimestampType(), True),
        StructField("merchant_category", StringType(), True),
        StructField("country_code", StringType(), True),
        StructField("risk_score", IntegerType(), True),
    ]
)

PAYMENT_SCHEMA = StructType(
    [
        StructField("payment_id", StringType(), True),
        StructField("account_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("transaction_amount", StringType(), True),
        StructField("currency_code", StringType(), True),
        StructField("transaction_status", StringType(), True),
        StructField("event_timestamp", TimestampType(), True),
        StructField("processing_timestamp", TimestampType(), True),
        StructField("counterparty_account_id", StringType(), True),
        StructField("country_code", StringType(), True),
        StructField("risk_score", IntegerType(), True),
    ]
)

TRADE_SCHEMA = StructType(
    [
        StructField("trade_id", StringType(), True),
        StructField("account_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("security_id", StringType(), True),
        StructField("quantity", StringType(), True),
        StructField("price", StringType(), True),
        StructField("transaction_amount", StringType(), True),
        StructField("currency_code", StringType(), True),
        StructField("side", StringType(), True),
        StructField("transaction_status", StringType(), True),
        StructField("event_timestamp", TimestampType(), True),
        StructField("processing_timestamp", TimestampType(), True),
        StructField("country_code", StringType(), True),
        StructField("risk_score", IntegerType(), True),
    ]
)

BALANCE_SCHEMA = StructType(
    [
        StructField("balance_id", StringType(), True),
        StructField("account_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("balance_date", TimestampType(), True),
        StructField("opening_balance", StringType(), True),
        StructField("closing_balance", StringType(), True),
        StructField("currency_code", StringType(), True),
    ]
)

SCHEMA_BY_DATASET = {
    "customers": CUSTOMER_SCHEMA,
    "accounts": ACCOUNT_SCHEMA,
    "securities": SECURITY_SCHEMA,
    "transactions": TRANSACTION_SCHEMA,
    "payments": PAYMENT_SCHEMA,
    "trades": TRADE_SCHEMA,
    "daily_account_balances": BALANCE_SCHEMA,
}

