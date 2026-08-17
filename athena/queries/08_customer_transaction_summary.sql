-- Run in Amazon Athena
-- Customer-level spending and activity summary.
SELECT
  c.customer_id,
  c.full_name,
  c.email,
  c.risk_score AS customer_risk_score,
  COUNT(t.transaction_id) AS transaction_count,
  SUM(t.transaction_amount) AS total_transaction_amount,
  AVG(t.transaction_amount) AS avg_transaction_amount,
  MAX(t.event_timestamp) AS latest_transaction_timestamp
FROM fdp_dev_batch_lakehouse.gold_dim_customer c
LEFT JOIN fdp_dev_batch_lakehouse.gold_fact_transaction t
  ON c.customer_id = t.customer_id
GROUP BY 1, 2, 3, 4
ORDER BY total_transaction_amount DESC NULLS LAST;
