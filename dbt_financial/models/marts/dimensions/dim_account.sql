select
  account_id,
  customer_id,
  account_type,
  currency_code,
  current_balance,
  opened_at,
  status
from {{ ref('stg_accounts') }}

