output "data_lake_bucket_name" {
  description = "S3 streaming data lake bucket name."
  value       = aws_s3_bucket.streaming_data_lake.id
}

output "glue_database_name" {
  description = "Glue catalog database name."
  value       = module.glue_catalog.database_name
}
