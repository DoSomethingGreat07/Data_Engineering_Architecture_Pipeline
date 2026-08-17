data "aws_iam_policy_document" "deny_insecure_transport" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.this.arn,
      "${aws_s3_bucket.this.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

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

resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id
  policy = data.aws_iam_policy_document.deny_insecure_transport.json
}

resource "aws_s3_object" "prefixes" {
  for_each               = toset(var.prefixes)
  bucket                 = aws_s3_bucket.this.id
  key                    = "${trim(each.value, "/")}/"
  content                = ""
  server_side_encryption = "aws:kms"
  kms_key_id             = var.kms_key_arn
}
