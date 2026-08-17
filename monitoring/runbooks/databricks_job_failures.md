# Databricks Job Failures

Alert meaning:
- Batch or streaming Databricks job execution failed.

First checks:
- Review job run output in Databricks.
- Confirm cluster policy, runtime version, and attached permissions.
- Check the input S3 paths and checkpoint locations.

Detailed investigation:
- Verify Delta read/write paths are reachable.
- Review Great Expectations validation outputs for the same execution window.
- Check for schema drift or malformed input files.
- Confirm cluster auto-termination did not interrupt long-running work unexpectedly.

Likely root causes:
- Bad input data
- Missing cloud access to S3 or Kinesis
- Delta schema mismatch
- Runtime package or connector issue

Recovery steps:
- Fix the data or configuration problem.
- Restart the job using the same checkpoint for streaming.
- Confirm no duplicate write side effects before replaying a batch.

Escalation:
- Escalate if the failure repeats with unchanged input and config.

