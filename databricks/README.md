# Databricks Phase 3

This directory contains the batch pipeline implementation for Bronze to Silver and Gold processing.

Main entrypoint:
- `databricks/batch/financial_batch_pipeline.py`

Run in Databricks:
- Create a job or notebook task that executes the Python file with runtime parameters.
- Mount or directly reference the S3 bucket created by Terraform.
- Use a job cluster with auto-termination to control cost.

Example parameters:

```text
--bronze-root s3://<bucket>/batch/raw
--silver-root s3://<bucket>/batch/silver
--gold-root s3://<bucket>/batch/gold
--rejected-root s3://<bucket>/batch/rejected
--run-date 2026-08-15
```

Local validation notes:
- The transformation helper functions are unit-tested locally.
- End-to-end Spark job execution requires a Spark runtime and is treated as an integration validation step.

