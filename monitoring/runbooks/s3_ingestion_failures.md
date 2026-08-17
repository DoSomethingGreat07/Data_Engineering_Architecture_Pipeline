# S3 Ingestion Failures

Alert meaning:
- Batch files failed to upload into the S3 Bronze path.

First checks:
- Confirm the batch producer logs in CloudWatch.
- Verify the AWS profile or IAM role in use by the producer.
- Check the target bucket name and raw prefix configuration.

Detailed investigation:
- Inspect the latest producer log entries for `failed to upload` or retry exhaustion.
- Confirm the bucket exists and the prefix is correct.
- Check KMS key permissions for `kms:Encrypt` and `kms:GenerateDataKey`.
- Confirm the role has `s3:PutObject`, `s3:ListBucket`, and bucket policy access.

Likely root causes:
- Incorrect bucket name or prefix
- Missing IAM permissions
- KMS key access denied
- Temporary AWS or network failure

Recovery steps:
- Correct the configuration and rerun the batch producer.
- Reprocess the source file only after confirming it was not partially ingested.
- If retryable failures were transient, rerun the ingestion job idempotently.

Escalation:
- Escalate if failures persist across multiple files after IAM and KMS validation.

