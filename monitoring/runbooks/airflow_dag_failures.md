# Airflow DAG Failures

Alert meaning:
- A batch or streaming operations DAG task failed or timed out.

First checks:
- Inspect the failed task in the Airflow UI.
- Review retries, execution timeout, and upstream task states.
- Check whether the failure occurred in Databricks, Snowflake, dbt, or validation logic.

Detailed investigation:
- Confirm the Airflow connection IDs are configured.
- Review task logs for provider-specific authentication or SQL errors.
- Validate that any generated validation result files exist where expected.

Likely root causes:
- Missing Airflow connection or variable
- Upstream platform failure
- SQL/script error in a downstream step
- Task timeout caused by external system slowness

Recovery steps:
- Correct the connection or parameter issue.
- Clear and rerun only the affected tasks if downstream idempotency is preserved.

Escalation:
- Escalate if multiple unrelated DAGs begin failing at the same time.

