# Snowflake Phase 7

This directory contains Snowflake SQL and operating notes for loading validated Gold data into Snowflake.

Run locations:

- `setup/` and `ddl/`: run in Snowflake worksheets or via SnowSQL.
- `loading/`: run in Snowflake after the S3 stage is configured.
- `validation/`: run in Snowflake to reconcile Snowflake against the lake outputs.

Important trust-model note:

Snowflake S3 storage integrations require a two-step setup:

1. Create the storage integration in Snowflake.
2. Inspect the generated Snowflake IAM identity and external ID, then update the AWS IAM trust policy to allow that Snowflake-generated principal.

Do not hardcode generated Snowflake IAM user values in repository SQL.

