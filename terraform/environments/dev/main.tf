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

data "aws_caller_identity" "current" {}

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
    "streaming/raw",
    "streaming/rejected",
    "streaming/silver",
    "streaming/gold",
    "streaming/checkpoints",
  ]
}

module "kms" {
  source = "../../modules/kms"

  project_name            = var.project_name
  environment             = var.environment
  aws_region              = var.aws_region
  kms_alias_name          = var.kms_alias_name
  deletion_window_in_days = var.kms_deletion_window_days
  tags                    = local.common_tags
}

module "networking" {
  source = "../../modules/networking"

  project_name                      = var.project_name
  environment                       = var.environment
  vpc_cidr                          = var.vpc_cidr
  availability_zones                = var.availability_zones
  private_subnet_cidrs              = var.private_subnet_cidrs
  enable_kinesis_interface_endpoint = var.enable_kinesis_interface_endpoint
  tags                              = local.common_tags
}

module "data_lake" {
  source = "../../modules/data_lake"

  bucket_name                        = var.data_lake_bucket_name
  kms_key_arn                        = module.kms.key_arn
  prefixes                           = local.data_lake_prefixes
  noncurrent_version_expiration_days = var.s3_noncurrent_version_expiration_days
  transition_to_ia_days              = var.s3_transition_to_ia_days
  glacier_transition_days            = var.s3_glacier_transition_days
  tags                               = local.common_tags
}

module "kinesis" {
  source = "../../modules/kinesis"

  stream_name            = var.kinesis_stream_name
  kms_key_id             = module.kms.key_arn
  shard_count            = var.kinesis_shard_count
  retention_period_hours = var.kinesis_retention_period_hours
  stream_mode            = var.kinesis_stream_mode
  tags                   = local.common_tags
}

module "glue_catalog" {
  source = "../../modules/glue_catalog"

  database_name = var.glue_database_name
  description   = "Glue catalog database for ${var.project_name} ${var.environment}."
  tags          = local.common_tags
}

module "cloudwatch" {
  source = "../../modules/cloudwatch"

  project_name            = var.project_name
  environment             = var.environment
  kms_key_id              = module.kms.key_arn
  log_retention_days      = var.log_retention_days
  kinesis_stream_name     = module.kinesis.stream_name
  alarm_actions           = var.alarm_actions
  custom_metric_namespace = var.custom_metric_namespace
  custom_metric_filters   = var.custom_metric_filters
  tags                    = local.common_tags
}

module "iam" {
  source = "../../modules/iam"

  project_name       = var.project_name
  environment        = var.environment
  bucket_arn         = module.data_lake.bucket_arn
  kinesis_stream_arn = module.kinesis.stream_arn
  glue_database_arn  = "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${module.glue_catalog.database_name}"
  kms_key_arn        = module.kms.key_arn
  cloudwatch_log_group_arns = [
    for name in module.cloudwatch.log_group_names :
    "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:${name}"
  ]
  runtime_service_principals = var.runtime_service_principals
  runtime_role_arns          = var.runtime_role_arns
  github_oidc_provider_arn   = var.github_oidc_provider_arn
  github_repositories        = var.github_repositories
  tags                       = local.common_tags
}
