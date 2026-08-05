# SSE-S3 (AES256) for this slice. SSE-KMS with a customer-managed key is a
# documented future migration for finer-grained key rotation and audit —
# no aws_kms_key (or any KMS resource) is created here. var.encryption_mode
# is constrained to "sse_s3" only until that migration is designed.
#
# bucket_key_enabled is deliberately false: S3 Bucket Keys reduce KMS request
# costs under SSE-KMS and are not applicable to SSE-S3 (AES256). Enabling the
# flag here would imply a KMS posture that does not exist.

resource "aws_s3_bucket_server_side_encryption_configuration" "community_data_lake" {
  bucket = aws_s3_bucket.community_data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = false
  }
}
