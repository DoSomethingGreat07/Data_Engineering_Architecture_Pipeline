-- Run in Amazon Athena
-- Account-level transaction volume and balance view.
WITH latest_balances AS (
  SELECT
    account_id,
    max(balance_date) AS latest_balance_date,
    max_by(closing_balance, balance_date) AS latest_closing_balance
  FROM fdp_dev_batch_lakehouse.gold_fact_daily_account_balance
  GROUP BY 1
)
SELECT
  a.account_id,
  a.account_type,
  a.status,
  lb.latest_balance_date,
  lb.latest_closing_balance,
  COUNT(t.transaction_id) AS transaction_count,
  SUM(t.transaction_amount) AS total_transaction_amount
FROM fdp_dev_batch_lakehouse.gold_dim_account a
LEFT JOIN latest_balances lb
  ON a.account_id = lb.account_id
LEFT JOIN fdp_dev_batch_lakehouse.gold_fact_transaction t
  ON a.account_id = t.account_id
GROUP BY 1, 2, 3, 4, 5
ORDER BY total_transaction_amount DESC NULLS LAST;
