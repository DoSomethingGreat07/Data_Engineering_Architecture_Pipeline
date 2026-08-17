# QuickSight Dashboard Specification

## Connection

- Service: Amazon QuickSight
- Connector: Amazon Athena
- Catalog: `awsdatacatalog`
- Database: `fdp_dev_batch_analytics_marts`
- Recommended datasets:
  - `mart_financial_performance`
  - `mart_customer_risk`
  - `mart_regulatory_reconciliation`

## Business Questions

- How much value and volume did the latest batch process?
- Which customers and countries carry the greatest risk concentration?
- Did the latest batch reconcile within acceptable tolerance?

## Dataset Strategy

- Use Athena direct query first for simplicity.
- Move to SPICE if dashboard performance or concurrency becomes a bottleneck.
- Keep the marts as the only QuickSight-facing datasets to avoid exposing raw table complexity.

## Analysis 1: Financial Performance

- KPIs:
  - total transaction amount
  - transaction count
  - average transaction amount
- Visuals:
  - daily line chart by `processing_date`
  - stacked bar by `currency_code`
  - summary table by date and currency
- Filters:
  - processing date
  - currency code

## Analysis 2: Customer Risk

- KPIs:
  - high risk customers
  - total amount linked to high risk customers
- Visuals:
  - scatterplot of `customer_risk_score` vs `total_transaction_amount`
  - heatmap by `country_code`
  - top-risk customer table
- Filters:
  - country code
  - customer risk score band

## Analysis 3: Regulatory Reconciliation

- KPIs:
  - debit credit difference
  - transaction count
  - net flow imbalance ratio
- Visuals:
  - line chart for `debit_credit_difference`
  - exception table for high imbalance dates
- Filters:
  - processing date

## Calculated Fields

- `Average Ticket Size`
  - `sum({total_transaction_amount}) / sum({transaction_count})`
- `High Risk Customer Flag`
  - `ifelse({customer_risk_score} >= 80 OR {max_transaction_risk_score} >= 80, 'High', 'Normal')`
- `Reconciliation Gap Flag`
  - `ifelse({debit_credit_difference} > 1000, 'Investigate', 'Normal')`
- `Batch Health Status`
  - `ifelse({net_flow_imbalance_ratio} > 0.75, 'Critical', ifelse({net_flow_imbalance_ratio} > 0.40, 'Warning', 'Healthy'))`

## Setup Checklist

1. Enable QuickSight in the target AWS account and region.
2. In Manage QuickSight, grant access to Athena and the S3 query results bucket.
3. If required, enable the AWS Glue Data Catalog connector.
4. Create Athena datasets from the three marts.
5. Build analyses and publish dashboards.
6. Refresh the datasets after successful Airflow batch runs.
