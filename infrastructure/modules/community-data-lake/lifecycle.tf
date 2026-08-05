# Retention defaults (accepted_retention_days, quarantine_retention_days) are
# review-required starting points, not validated production policy. Each
# prefix-scoped retention rule is independent so raw/ and quarantine/ can be
# retired on different schedules. Slice 8.10 formalizes this contract and adds
# explicit expired-delete-marker cleanup so versioning does not retain
# delete markers indefinitely.

resource "aws_s3_bucket_lifecycle_configuration" "community_data_lake" {
  bucket = aws_s3_bucket.community_data_lake.id

  # Lifecycle configuration requires versioning to already be configured.
  depends_on = [aws_s3_bucket_versioning.community_data_lake]

  rule {
    id     = "accepted-retention"
    status = "Enabled"

    filter {
      prefix = local.accepted_prefix
    }

    expiration {
      days = var.accepted_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }

  rule {
    id     = "quarantine-retention"
    status = "Enabled"

    filter {
      prefix = local.quarantine_prefix
    }

    expiration {
      days = var.quarantine_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }

  # Bucket-wide: incomplete multipart uploads can occur under either prefix.
  # Kept as a separate rule (empty filter) rather than duplicated under each
  # prefix rule — multipart initiation is not prefix-bound in practice.
  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = var.incomplete_multipart_days
    }
  }

  # Bucket-wide: when a current version expires under a versioned bucket, S3
  # creates a delete marker. This rule removes *expired* delete markers
  # (markers with no remaining noncurrent versions). It must stay a separate
  # rule — AWS does not allow combining expired_object_delete_marker with
  # expiration.days in the same expiration block.
  rule {
    id     = "expire-delete-markers"
    status = "Enabled"

    filter {}

    expiration {
      expired_object_delete_marker = true
    }
  }
}
