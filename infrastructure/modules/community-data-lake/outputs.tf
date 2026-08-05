output "bucket_name" {
  description = "Community Data Lake bucket name."
  value       = aws_s3_bucket.community_data_lake.bucket
}

output "bucket_arn" {
  description = "Community Data Lake bucket ARN."
  value       = aws_s3_bucket.community_data_lake.arn
}

output "bucket_region" {
  description = "AWS region the bucket was created in."
  value       = aws_s3_bucket.community_data_lake.region
}

output "accepted_prefix" {
  description = "Key prefix for accepted objects."
  value       = local.accepted_prefix
}

output "quarantine_prefix" {
  description = "Key prefix for quarantined objects."
  value       = local.quarantine_prefix
}

output "writer_policy_arn" {
  description = "ARN of the least-privilege writer policy (not attached to any role in this slice)."
  value       = aws_iam_policy.writer.arn
}

output "writer_policy_name" {
  description = "Name of the least-privilege writer policy (not attached to any role in this slice)."
  value       = aws_iam_policy.writer.name
}

output "encryption_mode" {
  description = "Server-side encryption mode in effect."
  value       = var.encryption_mode
}

output "enable_ingestion_wire" {
  description = "Always false in this slice: bucket existence does not enable ingestion."
  value       = var.enable_ingestion_wire
}
