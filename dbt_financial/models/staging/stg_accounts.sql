select
  account_id,
  customer_id,
  account_type,
  currency_code,
  current_balance,
  cast(opened_at as timestamp) as opened_at,
  status,
  cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
  source_file,
  processing_date
from {{ source('lakehouse', 'silver_accounts') }}
