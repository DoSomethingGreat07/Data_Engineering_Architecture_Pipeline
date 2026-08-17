variable "project_name" {
  description = "Project name used in resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "aws_region" {
  description = "AWS region where the KMS key is deployed."
  type        = string
}

variable "kms_alias_name" {
  description = "Alias suffix for the customer-managed key."
  type        = string
}

variable "deletion_window_in_days" {
  description = "KMS deletion window."
  type        = number
  default     = 30
}

variable "enable_key_rotation" {
  description = "Whether to enable KMS key rotation."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}
