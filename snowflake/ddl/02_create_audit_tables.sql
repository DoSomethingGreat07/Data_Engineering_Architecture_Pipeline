-- Run in Snowflake

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.AUDIT.LOAD_HISTORY (
  load_id STRING,
  source_object STRING,
  target_table STRING,
  stage_name STRING,
  copy_statement STRING,
  load_started_at TIMESTAMP_NTZ,
  load_finished_at TIMESTAMP_NTZ,
  status STRING,
  rows_loaded NUMBER(18,0),
  rows_parsed NUMBER(18,0),
  error_count NUMBER(18,0),
  error_limit NUMBER(18,0),
  first_error STRING
);

CREATE TABLE IF NOT EXISTS FINANCIAL_DATA.AUDIT.RECONCILIATION_RESULTS (
  reconciliation_id STRING,
  dataset_name STRING,
  source_row_count NUMBER(18,0),
  target_row_count NUMBER(18,0),
  row_count_difference NUMBER(18,0),
  source_amount_sum NUMBER(18,2),
  target_amount_sum NUMBER(18,2),
  amount_difference NUMBER(18,2),
  duplicate_identifier_count NUMBER(18,0),
  rejected_record_count NUMBER(18,0),
  checked_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  status STRING,
  details STRING
);

