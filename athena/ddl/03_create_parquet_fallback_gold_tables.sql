-- Run in Amazon Athena
-- Use these only if your environment cannot query the primary Delta layout reliably.
-- This fallback does not replace the Delta lakehouse; it provides Athena-compatible published Gold tables.

CREATE EXTERNAL TABLE IF NOT EXISTS financial_data_lakehouse.fact_transaction_parquet (
  transaction_id string,
  account_id string,
  customer_id string,
  transaction_type string,
  transaction_amount decimal(18,2),
  currency_code string,
  transaction_status string,
  event_timestamp timestamp,
  processing_timestamp timestamp,
  merchant_category string,
  country_code string,
  risk_score int,
  ingestion_timestamp timestamp
)
PARTITIONED BY (processing_date date)
STORED AS PARQUET
LOCATION 's3://<data-lake-bucket>/athena/gold/fact_transaction_parquet/';
