-- Run in Amazon Athena
-- Daily transaction status breakdown for the live dataset.
SELECT
  date(event_timestamp) AS transaction_date,
  transaction_status,
  COUNT(*) AS transaction_count,
  SUM(transaction_amount) AS total_transaction_amount
FROM fdp_dev_batch_lakehouse.gold_fact_transaction
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
