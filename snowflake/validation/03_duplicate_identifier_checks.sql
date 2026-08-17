-- Run in Snowflake

SELECT
  transaction_id,
  COUNT(*) AS duplicate_count
FROM FINANCIAL_DATA.STAGING.FACT_TRANSACTION
GROUP BY transaction_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, transaction_id;

