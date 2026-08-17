# Reconciliation Mismatches

Alert meaning:
- Row counts, amount totals, duplicate rates, or debit/credit balances diverged between stages.

First checks:
- Run the Snowflake reconciliation SQL in `snowflake/validation/`.
- Review GX `gold_load_validation` outputs if available.
- Check whether rejected records increased unexpectedly.

Detailed investigation:
- Compare source RAW counts with staging and mart counts.
- Review duplicate IDs and late-arriving event handling.
- Inspect batch reruns or checkpoint restart history for replay effects.

Likely root causes:
- Duplicate replay
- Partial load into Snowflake
- Transformation bug
- Unexpected rejected-record spike

Recovery steps:
- Isolate the failing dataset and rerun the load/transformation idempotently.
- Correct duplicate handling or restart logic before replay.

Escalation:
- Escalate when mismatches persist after a clean rerun with verified source data.

