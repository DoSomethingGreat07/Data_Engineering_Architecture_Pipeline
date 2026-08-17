output "log_group_names" {
  description = "CloudWatch log groups created for the platform."
  value       = values(aws_cloudwatch_log_group.this)[*].name
}

