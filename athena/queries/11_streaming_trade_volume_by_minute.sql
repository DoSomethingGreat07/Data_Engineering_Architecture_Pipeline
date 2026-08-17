-- Run in Amazon Athena
SELECT
  trade_minute,
  security_id,
  side,
  trade_count,
  total_quantity,
  total_transaction_amount,
  avg_trade_price
FROM fdp_dev_streaming_lakehouse.gold_trade_minute_metrics
ORDER BY trade_minute DESC, security_id, side
LIMIT 200;

