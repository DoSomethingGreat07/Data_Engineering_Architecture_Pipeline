# Monitoring Phase 11

This directory contains CloudWatch monitoring definitions, custom metric helpers, and runbooks for the financial data platform.

Contents:
- `cloudwatch/metric_filters.json`
- `cloudwatch/custom_metrics_reference.md`
- `cloudwatch/sample_metric_payload.json`
- `runbooks/` operational investigation guides

Run locations:
- Terraform alarm resources: provisioned through `terraform/`
- Metric publishing utility: run from Python services or Airflow tasks
- Runbooks: operator documentation only

