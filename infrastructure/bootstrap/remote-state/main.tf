# Dedicated OpenTofu remote-state bucket controls (Slice 17.2).
#
# The bucket object itself is created/ensured by
# infrastructure/scripts/bootstrap-remote-state.sh via AWS CLI because the
# operator IAM user lacks s3:GetBucketPolicy / GetBucketTagging / GetBucketWebsite,
# which the aws_s3_bucket resource requires on every refresh.
#
# OpenTofu (local state) manages the required controls only:
# versioning, SSE-S3, public access block, ownership.

resource "aws_s3_bucket_versioning" "opentofu_state" {
  bucket = var.bucket_name

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "opentofu_state" {
  bucket = var.bucket_name

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "opentofu_state" {
  bucket = var.bucket_name

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "opentofu_state" {
  bucket = var.bucket_name

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}
