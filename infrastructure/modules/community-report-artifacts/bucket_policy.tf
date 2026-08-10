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
      aws_s3_bucket.report_artifacts.arn,
      "${aws_s3_bucket.report_artifacts.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "report_artifacts" {
  bucket = aws_s3_bucket.report_artifacts.id
  policy = data.aws_iam_policy_document.bucket_policy.json

  depends_on = [
    aws_s3_bucket_public_access_block.report_artifacts,
  ]
}
