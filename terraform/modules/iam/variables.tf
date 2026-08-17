variable "project_name" {
  description = "Project name used in naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "bucket_arn" {
  description = "S3 bucket ARN."
  type        = string
}

variable "kinesis_stream_arn" {
  description = "Kinesis stream ARN."
  type        = string
}

variable "glue_database_arn" {
  description = "Glue database ARN."
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN."
  type        = string
}

variable "cloudwatch_log_group_arns" {
  description = "CloudWatch log group ARNs."
  type        = list(string)
}

variable "runtime_service_principals" {
  description = "AWS service principals that can assume the runtime role."
  type        = list(string)
  default     = ["ec2.amazonaws.com"]
}

variable "runtime_role_arns" {
  description = "Additional principal ARNs that can assume the runtime role."
  type        = list(string)
  default     = []
}

variable "github_oidc_provider_arn" {
  description = "OIDC provider ARN for GitHub Actions deployment role."
  type        = string
  default     = null
}

variable "github_repositories" {
  description = "GitHub repositories allowed to assume the deployment role."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}

