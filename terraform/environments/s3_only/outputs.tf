output "data_lake_bucket_name" {
  description = "S3 batch data lake bucket name."
  value       = aws_s3_bucket.batch_data_lake.id
}

output "glue_database_name" {
  description = "Glue catalog database name."
  value       = module.glue_catalog.database_name
}

output "glue_table_names" {
  description = "Glue catalog Delta table names registered for the batch lakehouse."
  value       = sort([for table in aws_glue_catalog_table.delta_tables : table.name])
}
