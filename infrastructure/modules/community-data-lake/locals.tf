locals {
  name_prefix = "${var.project_name}-community-data-lake-${var.environment_name}"

  # Single private bucket, isolated by prefix rather than by separate buckets.
  bucket_name       = "${var.project_name}-community-data-lake-${var.environment_name}"
  accepted_prefix   = "raw/"
  quarantine_prefix = "quarantine/"

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment_name
      Component   = "community-data-lake"
      ManagedBy   = "opentofu"
      Ownership   = "platform-private"
    },
    var.tags
  )
}
