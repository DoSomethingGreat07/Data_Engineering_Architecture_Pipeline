# Custom Metrics Reference

These custom metrics are emitted by platform code and are intended for CloudWatch alarms and Airflow health reporting.

Namespace:
- `FinancialDataPlatform`

Metrics:
- `BatchIngestionFailures`
- `GreatExpectationsFailures`
- `ReconciliationMismatches`
- `DataFreshnessViolations`
- `KinesisWriteFailures`
- `StreamingMicroBatchFailures`
- `SnowflakeLoadFailures`
- `DbtTestFailures`

Recommended dimensions:
- `Environment`
- `DatasetName`
- `Stage`
- `SuiteName`
- `DagId`
- `TaskId`

