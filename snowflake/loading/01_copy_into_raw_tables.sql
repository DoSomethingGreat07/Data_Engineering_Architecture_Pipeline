-- Run in Snowflake
-- Replace the path patterns and load IDs per execution.

COPY INTO FINANCIAL_DATA.RAW.FACT_TRANSACTION_LANDING
FROM (
  SELECT
    $1:transaction_id::STRING,
    $1:account_id::STRING,
    $1:customer_id::STRING,
    $1:transaction_type::STRING,
    $1:transaction_amount::NUMBER(18,2),
    $1:currency_code::STRING,
    $1:transaction_status::STRING,
    $1:event_timestamp::TIMESTAMP_NTZ,
    $1:processing_timestamp::TIMESTAMP_NTZ,
    $1:merchant_category::STRING,
    $1:country_code::STRING,
    $1:risk_score::NUMBER(9,0),
    $1:ingestion_timestamp::TIMESTAMP_NTZ,
    $1:source_file::STRING,
    $1:processing_date::DATE,
    '<load-id>',
    CURRENT_TIMESTAMP()
  FROM @FINANCIAL_DATA.RAW.FDP_GOLD_STAGE/fact_transaction/
)
FILE_FORMAT = (FORMAT_NAME = FINANCIAL_DATA.RAW.PARQUET_FORMAT)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO FINANCIAL_DATA.RAW.FACT_PAYMENT_LANDING
FROM (
  SELECT
    $1:payment_id::STRING,
    $1:account_id::STRING,
    $1:customer_id::STRING,
    $1:transaction_amount::NUMBER(18,2),
    $1:currency_code::STRING,
    $1:transaction_status::STRING,
    $1:event_timestamp::TIMESTAMP_NTZ,
    $1:processing_timestamp::TIMESTAMP_NTZ,
    $1:counterparty_account_id::STRING,
    $1:country_code::STRING,
    $1:risk_score::NUMBER(9,0),
    $1:ingestion_timestamp::TIMESTAMP_NTZ,
    $1:source_file::STRING,
    $1:processing_date::DATE,
    '<load-id>',
    CURRENT_TIMESTAMP()
  FROM @FINANCIAL_DATA.RAW.FDP_GOLD_STAGE/fact_payment/
)
FILE_FORMAT = (FORMAT_NAME = FINANCIAL_DATA.RAW.PARQUET_FORMAT)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO FINANCIAL_DATA.RAW.FACT_TRADE_LANDING
FROM (
  SELECT
    $1:trade_id::STRING,
    $1:account_id::STRING,
    $1:customer_id::STRING,
    $1:security_id::STRING,
    $1:quantity::NUMBER(18,2),
    $1:price::NUMBER(18,2),
    $1:transaction_amount::NUMBER(18,2),
    $1:currency_code::STRING,
    $1:side::STRING,
    $1:transaction_status::STRING,
    $1:event_timestamp::TIMESTAMP_NTZ,
    $1:processing_timestamp::TIMESTAMP_NTZ,
    $1:country_code::STRING,
    $1:risk_score::NUMBER(9,0),
    $1:ingestion_timestamp::TIMESTAMP_NTZ,
    $1:source_file::STRING,
    $1:processing_date::DATE,
    '<load-id>',
    CURRENT_TIMESTAMP()
  FROM @FINANCIAL_DATA.RAW.FDP_GOLD_STAGE/fact_trade/
)
FILE_FORMAT = (FORMAT_NAME = FINANCIAL_DATA.RAW.PARQUET_FORMAT)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'ABORT_STATEMENT';

