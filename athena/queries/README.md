# Athena Query Notes

Run these queries in Amazon Athena against the deployed Glue database:
- `fdp_dev_batch_lakehouse`

Primary populated tables in the current Plaid-driven batch flow:
- `gold_fact_transaction`
- `gold_fact_daily_account_balance`
- `gold_dim_customer`
- `gold_dim_account`

Suggested run order:
1. `01_daily_transaction_totals.sql`
2. `03_high_risk_transactions.sql`
3. `08_customer_transaction_summary.sql`
4. `09_account_activity_summary.sql`
5. `10_member_cashflow_trend.sql`

Cost guidance:
- Filter on `processing_date` whenever possible for larger datasets.
- Keep Athena results under `s3://fdp-batch-only-nikhiljuluri-20260816/athena/results/`.
- Use workgroup data scan limits as the dataset grows.

Delta Lake note:
- These tables are backed by Delta Lake in S3.
- Athena reads the active Parquet files by using Glue metadata plus the Delta transaction log.
