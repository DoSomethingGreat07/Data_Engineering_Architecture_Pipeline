-- Run in Amazon Athena
-- Transaction counts and amounts by status.
SELECT
  transaction_status,
  COUNT(*) AS transaction_count,
  SUM(transaction_amount) AS total_transaction_amount,
  AVG(transaction_amount) AS avg_transaction_amount
FROM fdp_dev_batch_lakehouse.gold_fact_transaction
GROUP BY 1
ORDER BY transaction_count DESC;
