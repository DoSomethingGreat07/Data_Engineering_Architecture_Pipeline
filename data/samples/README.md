# Sample Data Notes

Generated sample datasets are written to `data/generated/` by the Phase 1 generator.

Batch outputs:
- `batch/customers.{csv,json}`
- `batch/accounts.{csv,json}`
- `batch/securities.{csv,json}`
- `batch/transactions.{csv,json}`
- `batch/payments.{csv,json}`
- `batch/trades.{csv,json}`
- `batch/daily_account_balances.{csv,json}`
- `batch/ingest_ready/<dataset>_20260815T120000Z.{csv,json}`

Streaming outputs:
- `streaming/events.jsonl`
- `streaming/malformed_events.jsonl`

The committed repository keeps only this note. Generated data is excluded by `.gitignore` so repeated runs stay local and deterministic.
