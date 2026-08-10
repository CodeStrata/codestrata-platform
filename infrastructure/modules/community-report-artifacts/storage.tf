# Private report-artifact bucket. Never served directly to browsers.
# Public URLs always go through reports.codestrata.ai → API → Lambda → GetObject.

resource "aws_s3_bucket" "report_artifacts" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy

  tags = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "report_artifacts" {
  bucket = aws_s3_bucket.report_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "report_artifacts" {
  bucket = aws_s3_bucket.report_artifacts.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "report_artifacts" {
  bucket = aws_s3_bucket.report_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}
