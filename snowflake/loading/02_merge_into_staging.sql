-- Run in Snowflake
-- These MERGE statements support idempotent incremental loading from RAW landing tables.

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.STAGING.FACT_TRANSACTION AS
SELECT * FROM FINANCIAL_DATA.RAW.FACT_TRANSACTION_LANDING WHERE 1 = 0;

MERGE INTO FINANCIAL_DATA.STAGING.FACT_TRANSACTION AS target
USING (
  SELECT *
  FROM FINANCIAL_DATA.RAW.FACT_TRANSACTION_LANDING
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY transaction_id
    ORDER BY processing_timestamp DESC, load_timestamp DESC
  ) = 1
) AS source
ON target.transaction_id = source.transaction_id
WHEN MATCHED THEN UPDATE SET
  account_id = source.account_id,
  customer_id = source.customer_id,
  transaction_type = source.transaction_type,
  transaction_amount = source.transaction_amount,
  currency_code = source.currency_code,
  transaction_status = source.transaction_status,
  event_timestamp = source.event_timestamp,
  processing_timestamp = source.processing_timestamp,
  merchant_category = source.merchant_category,
  country_code = source.country_code,
  risk_score = source.risk_score,
  ingestion_timestamp = source.ingestion_timestamp,
  source_file = source.source_file,
  processing_date = source.processing_date,
  load_id = source.load_id,
  load_timestamp = source.load_timestamp
WHEN NOT MATCHED THEN INSERT VALUES (
  source.transaction_id,
  source.account_id,
  source.customer_id,
  source.transaction_type,
  source.transaction_amount,
  source.currency_code,
  source.transaction_status,
  source.event_timestamp,
  source.processing_timestamp,
  source.merchant_category,
  source.country_code,
  source.risk_score,
  source.ingestion_timestamp,
  source.source_file,
  source.processing_date,
  source.load_id,
  source.load_timestamp
);

