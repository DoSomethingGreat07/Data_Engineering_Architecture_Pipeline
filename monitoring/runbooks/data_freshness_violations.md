# Data Freshness Violations

Alert meaning:
- Expected new data did not arrive on time for batch or streaming workloads.

First checks:
- Check the latest ingestion timestamps in S3/Delta/Snowflake.
- Confirm upstream generators or source jobs actually ran.
- Review Airflow scheduling and Databricks job completion time.

Detailed investigation:
- Compare source event time to processing time.
- Inspect Kinesis iterator age and streaming checkpoints.
- Review dbt source freshness if warehouse models are delayed.

Likely root causes:
- Upstream source delay
- Stalled streaming consumer
- Failed batch ingestion
- Snowflake or dbt downstream lag

Recovery steps:
- Restart stalled consumers or rerun delayed batch jobs.
- Revalidate the latest successful watermark before resuming downstream processing.

Escalation:
- Escalate when freshness breaches violate reporting or reconciliation SLAs.

