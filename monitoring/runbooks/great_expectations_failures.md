# Great Expectations Failures

Alert meaning:
- A validation suite failed for Bronze, Silver, Gold, or streaming micro-batch data.

First checks:
- Open the corresponding validation summary JSON under `great_expectations/results/`.
- Identify the failed suite, stage, and dataset.
- Check whether the issue is expected from synthetic bad-data scenarios or an unexpected regression.

Detailed investigation:
- Review the suite definition in `great_expectations/expectations/`.
- Compare row counts before and after validation.
- Inspect rejected records and recent schema changes.

Likely root causes:
- Missing required fields
- Invalid currency/status/type values
- Negative or out-of-range amounts
- Unexpected schema change

Recovery steps:
- Fix the upstream data generation or transformation logic.
- Re-run the affected validation and downstream stage only after the root cause is corrected.

Escalation:
- Escalate if a previously stable validation begins failing across multiple datasets.

