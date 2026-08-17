select
  t.transaction_id,
  t.account_id,
  t.customer_id,
  a.account_type,
  t.transaction_type,
  t.transaction_amount,
  t.currency_code,
  t.transaction_status,
  t.event_timestamp,
  t.processing_timestamp,
  t.merchant_category,
  t.country_code,
  t.risk_score,
  case when t.risk_score >= 80 then 'HIGH'
       when t.risk_score >= 50 then 'MEDIUM'
       else 'LOW'
  end as risk_band,
  t.processing_date
from {{ ref('stg_transactions') }} t
left join {{ ref('stg_accounts') }} a
  on t.account_id = a.account_id
