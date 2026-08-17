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
  description = "AWS profile name."
  type        = string
}

variable "data_lake_bucket_name" {
  description = "Globally unique S3 bucket name."
  type        = string
}

variable "glue_database_name" {
  description = "Glue catalog database name for the batch lakehouse."
  type        = string
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
