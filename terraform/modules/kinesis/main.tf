resource "aws_kinesis_stream" "this" {
  name             = var.stream_name
  shard_count      = var.stream_mode == "PROVISIONED" ? var.shard_count : null
  retention_period = var.retention_period_hours

  encryption_type = "KMS"
  kms_key_id      = var.kms_key_id

  stream_mode_details {
    stream_mode = var.stream_mode
  }

  tags = var.tags
}

