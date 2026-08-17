-- Run in Snowflake
-- Replace placeholders before execution.
-- Do not insert generated Snowflake IAM values here; those are discovered after creation.

CREATE STORAGE INTEGRATION IF NOT EXISTS FDP_S3_INT
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<aws-account-id>:role/<snowflake-storage-role>'
  ENABLED = TRUE
  STORAGE_ALLOWED_LOCATIONS = (
    's3://<data-lake-bucket>/batch/gold/',
    's3://<data-lake-bucket>/streaming/gold/'
  );

-- Inspect the generated Snowflake identity information:
DESC INTEGRATION FDP_S3_INT;

-- Optional validation after the AWS trust policy is updated:
-- SELECT SYSTEM$VALIDATE_STORAGE_INTEGRATION('FDP_S3_INT');

