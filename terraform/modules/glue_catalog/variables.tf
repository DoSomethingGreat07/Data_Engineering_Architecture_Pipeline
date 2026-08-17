variable "database_name" {
  description = "Glue catalog database name."
  type        = string
}

variable "description" {
  description = "Database description."
  type        = string
  default     = "Financial data platform lakehouse catalog."
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}

