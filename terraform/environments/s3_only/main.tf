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
      DataClass   = "SyntheticFinancialData"
    },
    var.additional_tags,
  )

  data_lake_prefixes = [
    "batch/raw",
    "batch/rejected",
    "batch/silver",
    "batch/gold",
  ]

  glue_delta_tables = {
    silver_customers = {
      name     = "silver_customers"
      location = "s3://${var.data_lake_bucket_name}/batch/silver/customers/"
      columns = [
        { name = "customer_id", type = "string" },
        { name = "full_name", type = "string" },
        { name = "email", type = "string" },
        { name = "country_code", type = "string" },
        { name = "risk_score", type = "int" },
        { name = "created_at", type = "timestamp" },
        { name = "ingestion_timestamp", type = "timestamp" },
        { name = "source_file", type = "string" },
      ]
    }
    silver_accounts = {
      name     = "silver_accounts"
      location = "s3://${var.data_lake_bucket_name}/batch/silver/accounts/"
      columns = [
        { name = "account_id", type = "string" },
        { name = "customer_id", type = "string" },
        { name = "account_type", type = "string" },
        { name = "currency_code", type = "string" },
        { name = "current_balance", type = "string" },
        { name = "opened_at", type = "timestamp" },
        { name = "status", type = "string" },
        { name = "ingestion_timestamp", type = "timestamp" },
        { name = "source_file", type = "string" },
      ]
    }
    silver_transactions = {
      name     = "silver_transactions"
      location = "s3://${var.data_lake_bucket_name}/batch/silver/transactions/"
      columns = [
        { name = "transaction_id", type = "string" },
        { name = "account_id", type = "string" },
        { name = "customer_id", type = "string" },
        { name = "transaction_type", type = "string" },
        { name = "transaction_amount", type = "decimal(18,2)" },
        { name = "currency_code", type = "string" },
        { name = "transaction_status", type = "string" },
        { name = "event_timestamp", type = "timestamp" },
        { name = "processing_timestamp", type = "timestamp" },
        { name = "merchant_category", type = "string" },
        { name = "country_code", type = "string" },
        { name = "risk_score", type = "int" },
        { name = "ingestion_timestamp", type = "timestamp" },
        { name = "source_file", type = "string" },
      ]
    }
    silver_daily_account_balances = {
      name     = "silver_daily_account_balances"
      location = "s3://${var.data_lake_bucket_name}/batch/silver/daily_account_balances/"
      columns = [
        { name = "balance_id", type = "string" },
        { name = "account_id", type = "string" },
        { name = "customer_id", type = "string" },
        { name = "balance_date", type = "timestamp" },
        { name = "opening_balance", type = "decimal(18,2)" },
        { name = "closing_balance", type = "decimal(18,2)" },
        { name = "currency_code", type = "string" },
        { name = "ingestion_timestamp", type = "timestamp" },
        { name = "source_file", type = "string" },
      ]
    }
    gold_dim_customer = {
      name     = "gold_dim_customer"
      location = "s3://${var.data_lake_bucket_name}/batch/gold/dim_customer/"
      columns = [
        { name = "customer_id", type = "string" },
        { name = "full_name", type = "string" },
        { name = "email", type = "string" },
        { name = "country_code", type = "string" },
        { name = "risk_score", type = "int" },
        { name = "created_at", type = "timestamp" },
        { name = "ingestion_timestamp", type = "timestamp" },
        { name = "source_file", type = "string" },
      ]
    }
    gold_dim_account = {
      name     = "gold_dim_account"
      location = "s3://${var.data_lake_bucket_name}/batch/gold/dim_account/"
      columns = [
        { name = "account_id", type = "string" },
        { name = "customer_id", type = "string" },
        { name = "account_type", type = "string" },
        { name = "currency_code", type = "string" },
        { name = "current_balance", type = "string" },
        { name = "opened_at", type = "timestamp" },
        { name = "status", type = "string" },
        { name = "ingestion_timestamp", type = "timestamp" },
        { name = "source_file", type = "string" },
      ]
    }
    gold_fact_transaction = {
      name     = "gold_fact_transaction"
      location = "s3://${var.data_lake_bucket_name}/batch/gold/fact_transaction/"
      columns = [
        { name = "transaction_id", type = "string" },
        { name = "account_id", type = "string" },
        { name = "customer_id", type = "string" },
        { name = "transaction_type", type = "string" },
        { name = "transaction_amount", type = "decimal(18,2)" },
        { name = "currency_code", type = "string" },
        { name = "transaction_status", type = "string" },
        { name = "event_timestamp", type = "timestamp" },
        { name = "processing_timestamp", type = "timestamp" },
        { name = "merchant_category", type = "string" },
        { name = "country_code", type = "string" },
        { name = "risk_score", type = "int" },
        { name = "ingestion_timestamp", type = "timestamp" },
        { name = "source_file", type = "string" },
      ]
    }
    gold_fact_daily_account_balance = {
      name     = "gold_fact_daily_account_balance"
      location = "s3://${var.data_lake_bucket_name}/batch/gold/fact_daily_account_balance/"
      columns = [
        { name = "balance_id", type = "string" },
        { name = "account_id", type = "string" },
        { name = "customer_id", type = "string" },
        { name = "balance_date", type = "timestamp" },
        { name = "opening_balance", type = "decimal(18,2)" },
        { name = "closing_balance", type = "decimal(18,2)" },
        { name = "currency_code", type = "string" },
        { name = "ingestion_timestamp", type = "timestamp" },
        { name = "source_file", type = "string" },
      ]
    }
  }
}

resource "aws_s3_bucket" "batch_data_lake" {
  bucket = var.data_lake_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "batch_data_lake" {
  bucket = aws_s3_bucket.batch_data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "batch_data_lake" {
  bucket                  = aws_s3_bucket.batch_data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "batch_data_lake" {
  bucket = aws_s3_bucket.batch_data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "batch_data_lake" {
  bucket = aws_s3_bucket.batch_data_lake.id

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
  for_each = toset(local.data_lake_prefixes)

  bucket  = aws_s3_bucket.batch_data_lake.id
  key     = "${trim(each.value, "/")}/"
  content = ""
}

module "glue_catalog" {
  source = "../../modules/glue_catalog"

  database_name = var.glue_database_name
  description   = "Glue catalog for the batch-only financial data lakehouse."
  tags          = local.common_tags
}

resource "aws_glue_catalog_table" "delta_tables" {
  for_each = local.glue_delta_tables

  name          = each.value.name
  database_name = module.glue_catalog.database_name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL                     = "TRUE"
    "spark.sql.sources.provider" = "delta"
  }

  storage_descriptor {
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    location      = each.value.location
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    dynamic "columns" {
      for_each = each.value.columns

      content {
        name = columns.value.name
        type = columns.value.type
      }
    }

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
      parameters = {
        path                   = each.value.location
        "serialization.format" = "1"
      }
    }
  }

  partition_keys {
    name = "processing_date"
    type = "date"
  }
}
