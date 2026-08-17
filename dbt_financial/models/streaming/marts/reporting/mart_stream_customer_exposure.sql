select
  processing_date,
  customer_id,
  account_id,
  security_id,
  currency_code,
  sum(case when side = 'BUY' then 1 else 0 end) as buy_trade_count,
  sum(case when side = 'SELL' then 1 else 0 end) as sell_trade_count,
  sum(case when side = 'BUY' then quantity else -quantity end) as net_quantity,
  sum(transaction_amount) as gross_notional_amount,
  avg(risk_score) as avg_risk_score,
  max(event_timestamp) as latest_event_timestamp
from {{ ref('fct_stream_trades') }}
group by 1, 2, 3, 4, 5
