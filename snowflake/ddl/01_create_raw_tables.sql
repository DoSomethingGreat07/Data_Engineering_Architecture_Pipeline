-- Run in Snowflake

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.RAW.FACT_TRANSACTION_LANDING (
  transaction_id STRING,
  account_id STRING,
  customer_id STRING,
  transaction_type STRING,
  transaction_amount NUMBER(18,2),
  currency_code STRING,
  transaction_status STRING,
  event_timestamp TIMESTAMP_NTZ,
  processing_timestamp TIMESTAMP_NTZ,
  merchant_category STRING,
  country_code STRING,
  risk_score NUMBER(9,0),
  ingestion_timestamp TIMESTAMP_NTZ,
  source_file STRING,
  processing_date DATE,
  load_id STRING,
  load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.RAW.FACT_PAYMENT_LANDING (
  payment_id STRING,
  account_id STRING,
  customer_id STRING,
  transaction_amount NUMBER(18,2),
  currency_code STRING,
  transaction_status STRING,
  event_timestamp TIMESTAMP_NTZ,
  processing_timestamp TIMESTAMP_NTZ,
  counterparty_account_id STRING,
  country_code STRING,
  risk_score NUMBER(9,0),
  ingestion_timestamp TIMESTAMP_NTZ,
  source_file STRING,
  processing_date DATE,
  load_id STRING,
  load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.RAW.FACT_TRADE_LANDING (
  trade_id STRING,
  account_id STRING,
  customer_id STRING,
  security_id STRING,
  quantity NUMBER(18,2),
  price NUMBER(18,2),
  transaction_amount NUMBER(18,2),
  currency_code STRING,
  side STRING,
  transaction_status STRING,
  event_timestamp TIMESTAMP_NTZ,
  processing_timestamp TIMESTAMP_NTZ,
  country_code STRING,
  risk_score NUMBER(9,0),
  ingestion_timestamp TIMESTAMP_NTZ,
  source_file STRING,
  processing_date DATE,
  load_id STRING,
  load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.RAW.DIM_CUSTOMER_LANDING (
  customer_id STRING,
  full_name STRING,
  email STRING,
  country_code STRING,
  risk_score NUMBER(9,0),
  created_at TIMESTAMP_NTZ,
  ingestion_timestamp TIMESTAMP_NTZ,
  source_file STRING,
  processing_date DATE,
  load_id STRING,
  load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.RAW.DIM_ACCOUNT_LANDING (
  account_id STRING,
  customer_id STRING,
  account_type STRING,
  currency_code STRING,
  current_balance NUMBER(18,2),
  opened_at TIMESTAMP_NTZ,
  status STRING,
  ingestion_timestamp TIMESTAMP_NTZ,
  source_file STRING,
  processing_date DATE,
  load_id STRING,
  load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.RAW.DIM_SECURITY_LANDING (
  security_id STRING,
  ticker STRING,
  security_name STRING,
  security_type STRING,
  exchange_code STRING,
  currency_code STRING,
  ingestion_timestamp TIMESTAMP_NTZ,
  source_file STRING,
  processing_date DATE,
  load_id STRING,
  load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.RAW.FACT_DAILY_ACCOUNT_BALANCE_LANDING (
  balance_id STRING,
  account_id STRING,
  customer_id STRING,
  balance_date TIMESTAMP_NTZ,
  opening_balance NUMBER(18,2),
  closing_balance NUMBER(18,2),
  currency_code STRING,
  ingestion_timestamp TIMESTAMP_NTZ,
  source_file STRING,
  processing_date DATE,
  load_id STRING,
  load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

