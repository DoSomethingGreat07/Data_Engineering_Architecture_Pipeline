output "data_lake_bucket_name" {
  description = "Data lake bucket name."
  value       = module.platform.data_lake_bucket_name
}

output "kinesis_stream_name" {
  description = "Kinesis stream name."
  value       = module.platform.kinesis_stream_name
}

output "glue_database_name" {
  description = "Glue database name."
  value       = module.platform.glue_database_name
}

