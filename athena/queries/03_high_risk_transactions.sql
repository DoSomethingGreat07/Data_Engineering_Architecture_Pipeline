-- Run in Amazon Athena
-- Highest-risk customer transactions from the Gold layer.
SELECT
  transaction_id,
  account_id,
  customer_id,
  transaction_amount,
  currency_code,
  merchant_category,
  transaction_status,
  risk_score,
  event_timestamp
FROM fdp_dev_batch_lakehouse.gold_fact_transaction
WHERE risk_score >= 30
ORDER BY risk_score DESC, transaction_amount DESC, event_timestamp DESC;
