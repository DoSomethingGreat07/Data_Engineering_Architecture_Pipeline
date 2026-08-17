select *
from {{ ref('mart_regulatory_reconciliation') }}
where coalesce(net_flow_imbalance_ratio, 0) > 0.75
