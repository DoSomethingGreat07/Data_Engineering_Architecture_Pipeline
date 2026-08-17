terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.66"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
      DataClass   = "StreamingFinancialMarketData"
    },
    var.additional_tags,
  )

  streaming_prefixes = [
    "streaming/raw",
    "streaming/rejected",
    "streaming/silver",
    "streaming/gold",
    "streaming/checkpoints",
    "athena/results",
  ]
}

resource "aws_s3_bucket" "streaming_data_lake" {
  bucket = var.data_lake_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "streaming_data_lake" {
  bucket = aws_s3_bucket.streaming_data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "streaming_data_lake" {
  bucket                  = aws_s3_bucket.streaming_data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "streaming_data_lake" {
  bucket = aws_s3_bucket.streaming_data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "streaming_data_lake" {
  bucket = aws_s3_bucket.streaming_data_lake.id

  rule {
    id     = "cost-control"
    status = "Enabled"

    filter {}

    transition {
      days          = var.transition_to_ia_days
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = var.glacier_transition_days
      storage_class = "GLACIER"
    }

    noncurrent_version_transition {
      noncurrent_days = 7
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}

resource "aws_s3_object" "prefixes" {
  for_each = toset(local.streaming_prefixes)

  bucket  = aws_s3_bucket.streaming_data_lake.id
  key     = "${trim(each.value, "/")}/"
  content = ""
}

module "glue_catalog" {
  source = "../../modules/glue_catalog"

  database_name = var.glue_database_name
  description   = "Glue catalog for the streaming-only financial market data lakehouse."
  tags          = local.common_tags
}
