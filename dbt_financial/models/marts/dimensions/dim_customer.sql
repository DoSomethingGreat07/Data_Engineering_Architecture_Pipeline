select
  customer_id,
  full_name,
  email,
  country_code,
  risk_score,
  created_at
from {{ ref('stg_customers') }}

