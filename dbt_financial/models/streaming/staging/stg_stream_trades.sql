with ranked as (
  select
    event_id,
    trade_id,
    account_id,
    customer_id,
    security_id,
    quantity,
    price,
    transaction_amount,
    currency_code,
    side,
    transaction_status,
    cast(event_timestamp as timestamp) as event_timestamp,
    cast(processing_timestamp as timestamp) as processing_timestamp,
    country_code,
    risk_score,
    cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
    processing_date,
    row_number() over (
      partition by event_id
      order by cast(processing_timestamp as timestamp) desc, cast(ingestion_timestamp as timestamp) desc
    ) as event_rank
  from {{ source('streaming_lakehouse', 'silver_trades') }}
)
select
  event_id,
  trade_id,
  account_id,
  customer_id,
  security_id,
  quantity,
  price,
  transaction_amount,
  currency_code,
  side,
  transaction_status,
  event_timestamp,
  processing_timestamp,
  country_code,
  risk_score,
  ingestion_timestamp,
  processing_date
from ranked
where event_rank = 1
