select
  balance_id,
  account_id,
  customer_id,
  cast(balance_date as timestamp) as balance_date,
  opening_balance,
  closing_balance,
  currency_code,
  cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
  source_file,
  processing_date
from {{ source('lakehouse', 'silver_daily_account_balances') }}
