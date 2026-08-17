variable "project_name" {
  description = "Project name used in naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "kms_key_id" {
  description = "KMS key ARN for log group encryption."
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention period."
  type        = number
  default     = 30
}

variable "kinesis_stream_name" {
  description = "Kinesis stream name for managed alarms."
  type        = string
}

variable "alarm_actions" {
  description = "Alarm action ARNs such as SNS topics."
  type        = list(string)
  default     = []
}

variable "custom_metric_namespace" {
  description = "Namespace for platform-emitted custom metrics."
  type        = string
  default     = "FinancialDataPlatform"
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}

variable "custom_metric_filters" {
  description = "Optional custom metric filters for log groups."
  type = list(object({
    log_group_name   = string
    metric_name      = string
    filter_pattern   = string
    metric_namespace = string
  }))
  default = []
}
