select
  balance_id,
  account_id,
  customer_id,
  balance_date,
  opening_balance,
  closing_balance,
  net_balance_change,
  currency_code,
  processing_date
from {{ ref('int_account_daily_balance') }}
