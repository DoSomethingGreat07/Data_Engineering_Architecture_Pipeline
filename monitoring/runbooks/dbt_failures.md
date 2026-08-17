# dbt Failures

Alert meaning:
- dbt parse, compile, build, or test steps failed.

First checks:
- Review dbt logs and the failing model or test.
- Confirm the Snowflake connection parameters and active role/warehouse.
- Identify whether the issue is SQL syntax, missing source object, or failed assertion.

Detailed investigation:
- Check the failing model lineage from sources through marts.
- Review freshness/source state in Snowflake RAW.
- Confirm required schemas and privileges exist.

Likely root causes:
- Missing RAW tables or wrong schema
- Failed relationship or accepted-values test
- Incremental model merge mismatch
- Warehouse or role privilege problem

Recovery steps:
- Fix the model, source, or permission problem.
- Re-run `dbt parse`, `dbt compile`, and then the failed build/test subset.

Escalation:
- Escalate if the failure is privilege-related and cannot be corrected within project-owned roles.

