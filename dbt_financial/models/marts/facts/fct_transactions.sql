select
  transaction_id,
  account_id,
  customer_id,
  account_type,
  transaction_type,
  transaction_amount,
  currency_code,
  transaction_status,
  event_timestamp,
  processing_timestamp,
  merchant_category,
  country_code,
  risk_score,
  risk_band,
  processing_date
from {{ ref('int_transaction_enrichment') }}
