select
  processing_date,
  count(*) as transaction_count,
  sum(case when transaction_type = 'DEBIT' then transaction_amount else 0 end) as debit_total,
  sum(case when transaction_type = 'CREDIT' then transaction_amount else 0 end) as credit_total,
  abs(
    sum(case when transaction_type = 'DEBIT' then transaction_amount else 0 end) -
    sum(case when transaction_type = 'CREDIT' then transaction_amount else 0 end)
  ) as debit_credit_difference,
  abs(
    sum(case when transaction_type = 'DEBIT' then transaction_amount else 0 end) -
    sum(case when transaction_type = 'CREDIT' then transaction_amount else 0 end)
  ) / nullif(
    sum(case when transaction_type in ('DEBIT', 'CREDIT') then transaction_amount else 0 end),
    0
  ) as net_flow_imbalance_ratio
from {{ ref('fct_transactions') }}
group by 1
