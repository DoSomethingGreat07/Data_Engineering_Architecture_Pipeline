-- Run in Snowflake
-- Replace the S3 rejected path with your actual rejected Delta or published file location if mirrored into Snowflake audit tables.

SELECT
  dataset_name,
  rejected_record_count,
  checked_at,
  status,
  details
FROM FINANCIAL_DATA.AUDIT.RECONCILIATION_RESULTS
WHERE rejected_record_count > 0
ORDER BY checked_at DESC;

