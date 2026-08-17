variable "bucket_name" {
  description = "Globally unique S3 bucket name."
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for bucket encryption."
  type        = string
}

variable "prefixes" {
  description = "Logical data lake prefixes."
  type        = list(string)
}

variable "noncurrent_version_expiration_days" {
  description = "Lifecycle setting for old object versions."
  type        = number
  default     = 30
}

variable "transition_to_ia_days" {
  description = "Transition current objects to standard-IA after this many days."
  type        = number
  default     = 30
}

variable "glacier_transition_days" {
  description = "Transition current objects to Glacier after this many days."
  type        = number
  default     = 90
}

variable "log_retention_days" {
  description = "Unused placeholder to keep module inputs aligned with platform config."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}

