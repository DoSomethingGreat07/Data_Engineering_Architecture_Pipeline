with accepted as (
  select
    processing_date,
    count(*) as accepted_trade_count,
    sum(transaction_amount) as accepted_notional_amount
  from {{ ref('fct_stream_trades') }}
  group by 1
),
rejected as (
  select
    processing_date,
    count(*) as rejected_event_count
  from {{ source('streaming_lakehouse', 'rejected_stream_events') }}
  group by 1
)
select
  accepted.processing_date,
  accepted.accepted_trade_count,
  accepted.accepted_notional_amount,
  coalesce(rejected.rejected_event_count, 0) as rejected_event_count,
  cast(coalesce(rejected.rejected_event_count, 0) as double) / nullif(accepted.accepted_trade_count + coalesce(rejected.rejected_event_count, 0), 0) as rejection_ratio
from accepted
left join rejected
  on accepted.processing_date = rejected.processing_date
