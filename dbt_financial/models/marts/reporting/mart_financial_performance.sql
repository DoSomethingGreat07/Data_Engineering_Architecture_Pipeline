select
  processing_date,
  cast(event_timestamp as date) as transaction_date,
  currency_code,
  merchant_category,
  transaction_type,
  sum(transaction_amount) as total_transaction_amount,
  count(*) as transaction_count,
  avg(transaction_amount) as avg_transaction_amount
from {{ ref('fct_transactions') }}
group by 1, 2, 3, 4, 5
