-- Run in Snowflake
-- Capture COPY load metadata for auditing after each load window.

INSERT INTO FINANCIAL_DATA.AUDIT.LOAD_HISTORY (
  load_id,
  source_object,
  target_table,
  stage_name,
  copy_statement,
  load_started_at,
  load_finished_at,
  status,
  rows_loaded,
  rows_parsed,
  error_count,
  error_limit,
  first_error
)
SELECT
  '<load-id>' AS load_id,
  file_name AS source_object,
  table_name AS target_table,
  stage_location AS stage_name,
  '<copy-statement-identifier>' AS copy_statement,
  last_load_time AS load_started_at,
  last_load_time AS load_finished_at,
  status,
  row_count AS rows_loaded,
  row_parsed AS rows_parsed,
  error_count,
  NULL AS error_limit,
  first_error_message AS first_error
FROM TABLE(
  INFORMATION_SCHEMA.COPY_HISTORY(
    TABLE_NAME => 'FINANCIAL_DATA.RAW.FACT_TRANSACTION_LANDING',
    START_TIME => DATEADD('hour', -1, CURRENT_TIMESTAMP())
  )
);

