select
  c.customer_id,
  c.full_name,
  c.country_code,
  c.risk_score as customer_risk_score,
  count(t.transaction_id) as transaction_count,
  sum(t.transaction_amount) as total_transaction_amount,
  avg(t.transaction_amount) as avg_transaction_amount,
  max(t.risk_score) as max_transaction_risk_score
from {{ ref('dim_customer') }} c
left join {{ ref('fct_transactions') }} t
  on c.customer_id = t.customer_id
group by 1, 2, 3, 4
