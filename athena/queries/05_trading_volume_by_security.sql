-- Run in Amazon Athena
-- Transaction amount distribution by merchant category.
SELECT
  merchant_category,
  COUNT(*) AS transaction_count,
  SUM(transaction_amount) AS total_transaction_amount,
  AVG(transaction_amount) AS avg_transaction_amount
FROM fdp_dev_batch_lakehouse.gold_fact_transaction
GROUP BY 1
ORDER BY total_transaction_amount DESC;
