locals {
  bucket_object_arn = "${var.bucket_arn}/*"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "runtime_assume_role" {
  dynamic "statement" {
    for_each = length(var.runtime_service_principals) > 0 ? [1] : []
    content {
      effect = "Allow"

      principals {
        type        = "Service"
        identifiers = var.runtime_service_principals
      }

      actions = ["sts:AssumeRole"]
    }
  }

  dynamic "statement" {
    for_each = length(var.runtime_role_arns) > 0 ? [1] : []
    content {
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = var.runtime_role_arns
      }

      actions = ["sts:AssumeRole"]
    }
  }
}

data "aws_iam_policy_document" "runtime_access" {
  statement {
    sid    = "S3DataLakeAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [
      var.bucket_arn,
      local.bucket_object_arn,
    ]
  }

  statement {
    sid    = "KinesisAccess"
    effect = "Allow"
    actions = [
      "kinesis:DescribeStream",
      "kinesis:DescribeStreamSummary",
      "kinesis:GetRecords",
      "kinesis:GetShardIterator",
      "kinesis:ListShards",
      "kinesis:PutRecord",
      "kinesis:PutRecords",
      "kinesis:SubscribeToShard",
    ]
    resources = [var.kinesis_stream_arn]
  }

  statement {
    sid    = "GlueCatalogRead"
    effect = "Allow"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:CreateTable",
      "glue:UpdateTable",
      "glue:BatchCreatePartition",
      "glue:GetPartitions",
    ]
    resources = [
      "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:catalog",
      var.glue_database_arn,
      "${var.glue_database_arn}/*",
    ]
  }

  statement {
    sid    = "KmsUsage"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = [var.kms_key_arn]
  }

  statement {
    sid    = "CloudWatchLogsWrite"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
    ]
    resources = [for arn in var.cloudwatch_log_group_arns : "${arn}:*"]
  }
}

resource "aws_iam_role" "runtime" {
  name               = "${var.project_name}-${var.environment}-runtime-role"
  assume_role_policy = data.aws_iam_policy_document.runtime_assume_role.json
  tags               = var.tags
}

resource "aws_iam_policy" "runtime" {
  name        = "${var.project_name}-${var.environment}-runtime-policy"
  description = "Least-privilege runtime access for the financial data platform."
  policy      = data.aws_iam_policy_document.runtime_access.json
  tags        = var.tags
}

resource "aws_iam_role_policy_attachment" "runtime" {
  role       = aws_iam_role.runtime.name
  policy_arn = aws_iam_policy.runtime.arn
}

data "aws_iam_policy_document" "deployment_assume_role" {
  count = var.github_oidc_provider_arn != null ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.github_oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [for repo in var.github_repositories : "repo:${repo}:*"]
    }
  }
}

resource "aws_iam_role" "deployment" {
  count = var.github_oidc_provider_arn != null ? 1 : 0

  name               = "${var.project_name}-${var.environment}-deployment-role"
  assume_role_policy = data.aws_iam_policy_document.deployment_assume_role[0].json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "deployment_runtime" {
  count = var.github_oidc_provider_arn != null ? 1 : 0

  role       = aws_iam_role.deployment[0].name
  policy_arn = aws_iam_policy.runtime.arn
}

