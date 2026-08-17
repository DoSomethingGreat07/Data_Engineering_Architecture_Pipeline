-- Run in Amazon Athena
-- These statements assume the Delta tables are registered in AWS Glue and stored in S3.
-- Keep the DDL minimal for Delta support.

CREATE EXTERNAL TABLE IF NOT EXISTS financial_data_lakehouse.dim_customer
LOCATION 's3://<data-lake-bucket>/batch/gold/dim_customer/'
TBLPROPERTIES ('table_type' = 'DELTA');

CREATE EXTERNAL TABLE IF NOT EXISTS financial_data_lakehouse.dim_account
LOCATION 's3://<data-lake-bucket>/batch/gold/dim_account/'
TBLPROPERTIES ('table_type' = 'DELTA');

CREATE EXTERNAL TABLE IF NOT EXISTS financial_data_lakehouse.fact_transaction
LOCATION 's3://<data-lake-bucket>/batch/gold/fact_transaction/'
TBLPROPERTIES ('table_type' = 'DELTA');

CREATE EXTERNAL TABLE IF NOT EXISTS financial_data_lakehouse.fact_daily_account_balance
LOCATION 's3://<data-lake-bucket>/batch/gold/fact_daily_account_balance/'
TBLPROPERTIES ('table_type' = 'DELTA');
