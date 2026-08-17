data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "kms" {
  statement {
    sid    = "EnableRootPermissions"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowCloudWatchLogsUsage"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["logs.${var.aws_region}.amazonaws.com"]
    }

    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
    ]
    resources = ["*"]

    condition {
      test     = "ArnLike"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values = [
        "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:*"
      ]
    }
  }
}

resource "aws_kms_key" "this" {
  description             = "${var.project_name} ${var.environment} data platform key"
  deletion_window_in_days = var.deletion_window_in_days
  enable_key_rotation     = var.enable_key_rotation
  policy                  = data.aws_iam_policy_document.kms.json
  tags                    = var.tags
}

resource "aws_kms_alias" "this" {
  name          = "alias/${var.kms_alias_name}"
  target_key_id = aws_kms_key.this.key_id
}
