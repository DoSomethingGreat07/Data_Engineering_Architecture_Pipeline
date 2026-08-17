select
  b.balance_id,
  b.account_id,
  b.customer_id,
  b.balance_date,
  b.opening_balance,
  b.closing_balance,
  b.closing_balance - b.opening_balance as net_balance_change,
  b.currency_code,
  b.processing_date
from {{ ref('stg_daily_balances') }} b
