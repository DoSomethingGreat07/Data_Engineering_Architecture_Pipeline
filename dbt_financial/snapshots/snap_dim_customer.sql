{% snapshot snap_dim_customer %}
{{
  config(
    target_schema='INTERMEDIATE',
    unique_key='customer_id',
    strategy='check',
    check_cols=['full_name', 'email', 'country_code', 'risk_score']
  )
}}

select * from {{ ref('dim_customer') }}

{% endsnapshot %}

