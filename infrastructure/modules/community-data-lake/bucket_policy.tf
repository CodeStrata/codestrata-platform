# Bucket policy for transport enforcement (Slice 8.12).
#
# DenyInsecureTransport rejects any request that does not use TLS
# (aws:SecureTransport = false). This is transport protection, not at-rest
# encryption (see encryption.tf / data-lake-encryption.md).
#
# Principal "*" with Effect Deny is the standard AWS pattern for this
# condition — it does not grant public Allow access. Public access remains
# blocked by aws_s3_bucket_public_access_block.

data "aws_iam_policy_document" "bucket_policy" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:*",
    ]

    resources = [
      aws_s3_bucket.community_data_lake.arn,
      "${aws_s3_bucket.community_data_lake.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "community_data_lake" {
  bucket = aws_s3_bucket.community_data_lake.id
  policy = data.aws_iam_policy_document.bucket_policy.json

  depends_on = [
    aws_s3_bucket_public_access_block.community_data_lake,
  ]
}
