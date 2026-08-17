output "runtime_role_arn" {
  description = "Runtime role ARN."
  value       = aws_iam_role.runtime.arn
}

output "deployment_role_arn" {
  description = "Deployment role ARN for GitHub Actions."
  value       = try(aws_iam_role.deployment[0].arn, null)
}

