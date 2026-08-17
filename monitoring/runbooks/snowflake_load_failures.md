# Snowflake Load Failures

Alert meaning:
- Snowflake `COPY INTO`, MERGE, or reconciliation steps failed.

First checks:
- Review Snowflake query history and copy history.
- Confirm the storage integration and stage are valid.
- Verify that the S3 path contains expected files.

Detailed investigation:
- Run `DESC INTEGRATION` and optional storage integration validation.
- Check the RAW landing table and audit table state.
- Review the `LOAD_HISTORY` audit table for errors and partial loads.

Likely root causes:
- AWS trust policy mismatch for the storage integration
- Stage path mismatch
- File format mismatch
- Duplicate or malformed payloads

Recovery steps:
- Fix the integration, stage, or file format issue.
- Re-run the load using a new load ID.
- Validate that partial landing data is reconciled before promoting downstream.

Escalation:
- Escalate if trust-policy setup is confirmed correct but Snowflake still cannot access S3.

