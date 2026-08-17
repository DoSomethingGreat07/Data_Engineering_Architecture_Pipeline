# Kinesis Write Failures

Alert meaning:
- The streaming producer failed to publish events to Kinesis or encountered throttling.

First checks:
- Review the stream producer logs.
- Check stream mode, shard count, and current write throughput.
- Validate the AWS role used by the producer.

Detailed investigation:
- Look for `failed to send event to Kinesis` messages.
- Check CloudWatch metrics for `WriteProvisionedThroughputExceeded`.
- Confirm the stream exists in the configured AWS Region.
- Validate IAM permissions for `kinesis:PutRecord` and `kinesis:PutRecords`.

Likely root causes:
- Provisioned shard capacity too low
- Wrong stream name or region
- Producer burst rate too high
- IAM access issue

Recovery steps:
- Reduce events per second for finite test runs.
- Increase shard count or switch to on-demand if approved.
- Restart the producer after correcting configuration.

Escalation:
- Escalate if throttling persists after throughput tuning or if the stream is unavailable.

