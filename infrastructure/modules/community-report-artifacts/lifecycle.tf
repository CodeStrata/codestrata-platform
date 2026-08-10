resource "aws_s3_bucket_lifecycle_configuration" "report_artifacts" {
  bucket = aws_s3_bucket.report_artifacts.id

  depends_on = [aws_s3_bucket_versioning.report_artifacts]

  # Application rotation enforces product current+previous retention.
  # S3 Versioning noncurrent expiration is operational recovery only.
  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = var.incomplete_multipart_days
    }
  }

  rule {
    id     = "staging-abandonment"
    status = "Enabled"

    filter {
      prefix = local.staging_prefix
    }

    expiration {
      days = var.staging_expiration_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }

  rule {
    id     = "noncurrent-ops-recovery"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }

  rule {
    id     = "expire-delete-markers"
    status = "Enabled"

    filter {}

    expiration {
      expired_object_delete_marker = true
    }
  }
}
