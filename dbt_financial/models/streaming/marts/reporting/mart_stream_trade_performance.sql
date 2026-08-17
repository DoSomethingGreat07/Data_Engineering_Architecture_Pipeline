select
  processing_date,
  trade_date,
  security_id,
  currency_code,
  side,
  sum(transaction_amount) as total_notional_amount,
  sum(quantity) as total_quantity,
  count(*) as trade_count,
  avg(price) as avg_trade_price,
  avg(risk_score) as avg_risk_score
from {{ ref('fct_stream_trades') }}
group by 1, 2, 3, 4, 5
