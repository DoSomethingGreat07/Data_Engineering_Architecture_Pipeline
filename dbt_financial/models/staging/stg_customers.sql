select
  customer_id,
  full_name,
  email,
  country_code,
  risk_score,
  cast(created_at as timestamp) as created_at,
  cast(ingestion_timestamp as timestamp) as ingestion_timestamp,
  source_file,
  processing_date
from {{ source('lakehouse', 'silver_customers') }}
