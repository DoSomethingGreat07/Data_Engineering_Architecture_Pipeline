-- Run in Amazon Athena
SELECT
  customer_id,
  account_id,
  security_id,
  buy_trade_count,
  sell_trade_count,
  net_quantity,
  gross_notional_amount,
  avg_risk_score,
  latest_event_timestamp
FROM fdp_dev_streaming_lakehouse.gold_customer_trade_exposure
ORDER BY gross_notional_amount DESC, latest_event_timestamp DESC
LIMIT 200;

