select
  transaction_id,
  account_id,
  customer_id,
  transaction_type,
  transaction_amount,
  currency_code,
  transaction_status,
  cast(event_timestamp as timestamp) as event_timestamp,
  cast(processing_timestamp as timestamp) as processing_timestamp,
  merchant_category,
  country_code,
  risk_score,
  cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
  source_file,
  processing_date
from {{ source('lakehouse', 'silver_transactions') }}
