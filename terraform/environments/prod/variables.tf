variable "project_name" {
  description = "Project name used in resource naming."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
}

variable "owner" {
  description = "Primary owner tag."
  type        = string
}

variable "cost_center" {
  description = "Cost center tag."
  type        = string
}

variable "additional_tags" {
  description = "Additional tags."
  type        = map(string)
  default     = {}
}

variable "aws_region" {
  description = "AWS region."
  type        = string
}

variable "aws_profile" {
  description = "AWS CLI profile name."
  type        = string
}

variable "data_lake_bucket_name" {
  description = "Globally unique S3 bucket name."
  type        = string
}

variable "kms_alias_name" {
  description = "Alias suffix for the customer-managed KMS key."
  type        = string
}

variable "kms_deletion_window_days" {
  description = "KMS deletion window."
  type        = number
  default     = 30
}

variable "kinesis_stream_name" {
  description = "Kinesis stream name."
  type        = string
}

variable "kinesis_shard_count" {
  description = "Kinesis shard count for provisioned mode."
  type        = number
  default     = 1
}

variable "kinesis_retention_period_hours" {
  description = "Kinesis retention period."
  type        = number
  default     = 24
}

variable "kinesis_stream_mode" {
  description = "Kinesis stream mode."
  type        = string
  default     = "PROVISIONED"
}

variable "glue_database_name" {
  description = "Glue database name."
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention days."
  type        = number
  default     = 30
}

variable "alarm_actions" {
  description = "Alarm action ARNs such as SNS topics."
  type        = list(string)
  default     = []
}

variable "custom_metric_namespace" {
  description = "Namespace for custom platform metrics."
  type        = string
  default     = "FinancialDataPlatform"
}

variable "vpc_cidr" {
  description = "VPC CIDR block."
  type        = string
}

variable "availability_zones" {
  description = "Availability zones for private subnets."
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks."
  type        = list(string)
}

variable "enable_kinesis_interface_endpoint" {
  description = "Whether to create a Kinesis interface VPC endpoint."
  type        = bool
  default     = true
}

variable "runtime_service_principals" {
  description = "AWS service principals allowed to assume the runtime role."
  type        = list(string)
  default     = ["ec2.amazonaws.com"]
}

variable "runtime_role_arns" {
  description = "Additional principal ARNs allowed to assume the runtime role."
  type        = list(string)
  default     = []
}

variable "github_oidc_provider_arn" {
  description = "GitHub OIDC provider ARN."
  type        = string
  default     = null
}

variable "github_repositories" {
  description = "Allowed GitHub repositories for OIDC deployment role."
  type        = list(string)
  default     = []
}

variable "s3_noncurrent_version_expiration_days" {
  description = "S3 lifecycle for noncurrent versions."
  type        = number
  default     = 30
}

variable "s3_transition_to_ia_days" {
  description = "Days before transition to Standard-IA."
  type        = number
  default     = 30
}

variable "s3_glacier_transition_days" {
  description = "Days before transition to Glacier."
  type        = number
  default     = 90
}

variable "custom_metric_filters" {
  description = "Optional custom CloudWatch log metric filters."
  type = list(object({
    log_group_name   = string
    metric_name      = string
    filter_pattern   = string
    metric_namespace = string
  }))
  default = []
}
