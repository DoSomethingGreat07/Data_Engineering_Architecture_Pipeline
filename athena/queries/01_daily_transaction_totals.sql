-- Run in Amazon Athena
-- Daily transaction volume and value by currency.
SELECT
  date(event_timestamp) AS transaction_date,
  currency_code,
  SUM(transaction_amount) AS total_transaction_amount,
  COUNT(*) AS transaction_count
FROM fdp_dev_batch_lakehouse.gold_fact_transaction
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
