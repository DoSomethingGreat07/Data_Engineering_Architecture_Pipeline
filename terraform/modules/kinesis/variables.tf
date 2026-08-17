variable "stream_name" {
  description = "Kinesis stream name."
  type        = string
}

variable "kms_key_id" {
  description = "KMS key ARN or ID for stream encryption."
  type        = string
}

variable "shard_count" {
  description = "Shard count for provisioned mode."
  type        = number
  default     = 1
}

variable "retention_period_hours" {
  description = "Kinesis retention period."
  type        = number
  default     = 24
}

variable "stream_mode" {
  description = "Kinesis stream mode."
  type        = string
  default     = "PROVISIONED"

  validation {
    condition     = contains(["PROVISIONED", "ON_DEMAND"], var.stream_mode)
    error_message = "stream_mode must be PROVISIONED or ON_DEMAND."
  }
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}

