resource "aws_s3_bucket_server_side_encryption_configuration" "report_artifacts" {
  bucket = aws_s3_bucket.report_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = false
  }
}
