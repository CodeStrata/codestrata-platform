check "foundation_fail_closed" {
  assert {
    condition     = var.environment_name == "production"
    error_message = "environment_name must be production in this slice."
  }

  assert {
    condition     = var.accepted_retention_days >= 30 && var.accepted_retention_days <= 2555
    error_message = "accepted_retention_days must be between 30 and 2555 days."
  }

  assert {
    condition     = var.quarantine_retention_days >= 7 && var.quarantine_retention_days <= 365
    error_message = "quarantine_retention_days must be between 7 and 365 days."
  }

  assert {
    condition     = var.quarantine_retention_days <= var.accepted_retention_days
    error_message = "quarantine_retention_days must be less than or equal to accepted_retention_days."
  }

  assert {
    condition     = var.incomplete_multipart_days >= 1 && var.incomplete_multipart_days <= 90
    error_message = "incomplete_multipart_days must be between 1 and 90 days."
  }

  assert {
    condition     = var.noncurrent_version_expiration_days >= 1 && var.noncurrent_version_expiration_days <= 2555
    error_message = "noncurrent_version_expiration_days must be between 1 and 2555 days."
  }

  assert {
    condition     = var.force_destroy == false
    error_message = "force_destroy must remain false by default for production Data Lake posture."
  }

  assert {
    condition     = var.encryption_mode == "sse_s3"
    error_message = "encryption_mode must be sse_s3 in this slice; SSE-KMS is a future migration."
  }
}
