-- Run in Amazon Athena
-- Cross-table row and amount summary for the currently populated Gold layer.
WITH transaction_summary AS (
  SELECT
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS transaction_amount_sum
  FROM fdp_dev_batch_lakehouse.gold_fact_transaction
), balance_summary AS (
  SELECT
    COUNT(*) AS balance_count,
    AVG(closing_balance) AS avg_closing_balance
  FROM fdp_dev_batch_lakehouse.gold_fact_daily_account_balance
)
SELECT
  transaction_count,
  transaction_amount_sum,
  balance_count,
  avg_closing_balance
FROM transaction_summary
CROSS JOIN balance_summary;
