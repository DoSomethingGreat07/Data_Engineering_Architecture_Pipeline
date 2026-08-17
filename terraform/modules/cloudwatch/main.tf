locals {
  log_groups = [
    "/financial-data-platform/${var.environment}/batch-producer",
    "/financial-data-platform/${var.environment}/stream-producer",
    "/financial-data-platform/${var.environment}/airflow",
    "/financial-data-platform/${var.environment}/databricks-batch",
    "/financial-data-platform/${var.environment}/databricks-streaming",
    "/financial-data-platform/${var.environment}/great-expectations",
  ]
}

resource "aws_cloudwatch_log_group" "this" {
  for_each = toset(local.log_groups)

  name              = each.value
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_id
  tags              = var.tags
}

resource "aws_cloudwatch_metric_alarm" "kinesis_write_failures" {
  alarm_name          = "${var.project_name}-${var.environment}-kinesis-write-throttling"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "WriteProvisionedThroughputExceeded"
  namespace           = "AWS/Kinesis"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert when Kinesis producers are throttled."
  alarm_actions       = var.alarm_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    StreamName = var.kinesis_stream_name
  }
}

resource "aws_cloudwatch_metric_alarm" "kinesis_iterator_age" {
  alarm_name          = "${var.project_name}-${var.environment}-kinesis-iterator-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "GetRecords.IteratorAgeMilliseconds"
  namespace           = "AWS/Kinesis"
  period              = 300
  statistic           = "Maximum"
  threshold           = 300000
  alarm_description   = "Alert when streaming consumers are lagging by more than 5 minutes."
  alarm_actions       = var.alarm_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    StreamName = var.kinesis_stream_name
  }
}

resource "aws_cloudwatch_metric_alarm" "custom_metric_alarms" {
  for_each = {
    ingestion_failures = {
      metric_name = "BatchIngestionFailures"
      threshold   = 1
      statistic   = "Sum"
    }
    ge_failures = {
      metric_name = "GreatExpectationsFailures"
      threshold   = 1
      statistic   = "Sum"
    }
    reconciliation_mismatches = {
      metric_name = "ReconciliationMismatches"
      threshold   = 1
      statistic   = "Sum"
    }
    freshness_violations = {
      metric_name = "DataFreshnessViolations"
      threshold   = 1
      statistic   = "Sum"
    }
  }

  alarm_name          = "${var.project_name}-${var.environment}-${replace(each.key, "_", "-")}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = each.value.metric_name
  namespace           = var.custom_metric_namespace
  period              = 300
  statistic           = each.value.statistic
  threshold           = each.value.threshold
  alarm_description   = "Platform custom metric alarm for ${each.value.metric_name}."
  alarm_actions       = var.alarm_actions
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_log_metric_filter" "custom_filters" {
  for_each = {
    for filter in var.custom_metric_filters :
    "${filter.log_group_name}-${filter.metric_name}" => filter
  }

  name           = replace(each.key, "/", "-")
  log_group_name = each.value.log_group_name
  pattern        = each.value.filter_pattern

  metric_transformation {
    name      = each.value.metric_name
    namespace = each.value.metric_namespace
    value     = "1"
  }
}
