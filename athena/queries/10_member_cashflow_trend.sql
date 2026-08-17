-- Run in Amazon Athena
-- Simple member cashflow trend by day and transaction type.
SELECT
  date(event_timestamp) AS transaction_date,
  transaction_type,
  COUNT(*) AS transaction_count,
  SUM(transaction_amount) AS total_transaction_amount
FROM fdp_dev_batch_lakehouse.gold_fact_transaction
GROUP BY 1, 2
ORDER BY transaction_date DESC, transaction_type;
