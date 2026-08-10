output "bucket_name" {
  description = "Community report artifact bucket name."
  value       = aws_s3_bucket.report_artifacts.bucket
}

output "bucket_arn" {
  description = "Community report artifact bucket ARN."
  value       = aws_s3_bucket.report_artifacts.arn
}

output "bucket_region" {
  description = "AWS region the bucket was created in."
  value       = aws_s3_bucket.report_artifacts.region
}

output "artifacts_prefix" {
  description = "Key prefix for published report artifacts."
  value       = local.artifacts_prefix
}

output "metadata_prefix" {
  description = "Key prefix for public-id and logical-index metadata."
  value       = local.metadata_prefix
}

output "staging_prefix" {
  description = "Key prefix for authenticated upload staging."
  value       = local.staging_prefix
}

output "runtime_policy_arn" {
  description = "ARN of the Lambda runtime policy for this bucket."
  value       = aws_iam_policy.runtime.arn
}

output "runtime_policy_name" {
  description = "Name of the Lambda runtime policy for this bucket."
  value       = aws_iam_policy.runtime.name
}

output "encryption_mode" {
  description = "Server-side encryption mode in effect."
  value       = var.encryption_mode
}

output "separate_from_data_lake" {
  description = "Always true — report artifacts must not share the Data Lake bucket."
  value       = true
}
