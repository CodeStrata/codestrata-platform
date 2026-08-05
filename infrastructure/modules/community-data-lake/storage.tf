# Single private bucket, isolated by prefix: raw/ (accepted) and
# quarantine/ (rejected or pending). No website hosting, no bucket ACLs,
# no CORS configuration — this bucket is never served directly to clients.

resource "aws_s3_bucket" "community_data_lake" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy

  tags = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "community_data_lake" {
  bucket = aws_s3_bucket.community_data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "community_data_lake" {
  bucket = aws_s3_bucket.community_data_lake.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "community_data_lake" {
  bucket = aws_s3_bucket.community_data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}
