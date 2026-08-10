check "report_artifacts_private" {
  assert {
    condition     = var.environment_name == "production"
    error_message = "environment_name must be production in this slice."
  }

  assert {
    condition     = var.force_destroy == false
    error_message = "force_destroy must remain false by default for production report artifacts."
  }

  assert {
    condition     = var.encryption_mode == "sse_s3"
    error_message = "encryption_mode must be sse_s3 in this slice."
  }

  assert {
    condition     = local.bucket_name != "codestrata-community-data-lake-production"
    error_message = "report artifact bucket must not reuse the Community Data Lake name."
  }
}
