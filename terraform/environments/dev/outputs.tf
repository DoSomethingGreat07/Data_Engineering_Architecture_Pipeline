output "data_lake_bucket_name" {
  description = "Data lake bucket name."
  value       = module.data_lake.bucket_id
}

output "kinesis_stream_name" {
  description = "Kinesis stream name."
  value       = module.kinesis.stream_name
}

output "glue_database_name" {
  description = "Glue database name."
  value       = module.glue_catalog.database_name
}

output "kms_key_arn" {
  description = "KMS key ARN."
  value       = module.kms.key_arn
}

output "runtime_role_arn" {
  description = "Runtime IAM role ARN."
  value       = module.iam.runtime_role_arn
}

output "deployment_role_arn" {
  description = "Deployment IAM role ARN."
  value       = module.iam.deployment_role_arn
}

output "private_subnet_ids" {
  description = "Private subnets."
  value       = module.networking.private_subnet_ids
}

