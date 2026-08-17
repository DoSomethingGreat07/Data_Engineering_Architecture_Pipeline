select *
from {{ ref('fct_transactions') }}
where transaction_amount < 0

