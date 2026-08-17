-- Run in Amazon Athena
-- Latest and average account balances by account.
SELECT
  account_id,
  max(balance_date) AS latest_balance_date,
  max_by(closing_balance, balance_date) AS latest_closing_balance,
  AVG(closing_balance) AS avg_closing_balance
FROM fdp_dev_batch_lakehouse.gold_fact_daily_account_balance
GROUP BY account_id
ORDER BY latest_closing_balance DESC;
