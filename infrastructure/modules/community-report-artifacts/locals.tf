locals {
  name_prefix = "${var.project_name}-community-report-artifacts-${var.environment_name}"

  # Dedicated private report-artifact bucket — NOT the Community Data Lake.
  bucket_name = "${var.project_name}-community-report-artifacts-${var.environment_name}"

  artifacts_prefix = "artifacts/"
  metadata_prefix  = "metadata/"
  staging_prefix   = "staging/"

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment_name
      Component   = "community-report-artifacts"
      ManagedBy   = "opentofu"
      Ownership   = "platform-private"
      Slice       = "17.16"
    },
    var.tags
  )
}
