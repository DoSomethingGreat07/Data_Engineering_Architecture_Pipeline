-- Run in Snowflake

SELECT
  load_id,
  target_table,
  status,
  rows_loaded,
  error_count,
  first_error,
  load_finished_at
FROM FINANCIAL_DATA.AUDIT.LOAD_HISTORY
ORDER BY load_finished_at DESC;

