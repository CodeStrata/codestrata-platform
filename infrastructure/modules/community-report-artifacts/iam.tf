# Least-privilege report-artifact access for Community Cloud Lambda.
# No ListBucket without prefix condition. No public grants.

data "aws_iam_policy_document" "runtime_policy" {
  statement {
    sid    = "ListApprovedReportPrefixes"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.report_artifacts.arn,
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        local.artifacts_prefix,
        "${local.artifacts_prefix}*",
        local.metadata_prefix,
        "${local.metadata_prefix}*",
        local.staging_prefix,
        "${local.staging_prefix}*",
      ]
    }
  }

  statement {
    sid    = "ManageReportArtifacts"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]

    resources = [
      "${aws_s3_bucket.report_artifacts.arn}/${local.artifacts_prefix}*",
      "${aws_s3_bucket.report_artifacts.arn}/${local.metadata_prefix}*",
      "${aws_s3_bucket.report_artifacts.arn}/${local.staging_prefix}*",
    ]
  }
}

resource "aws_iam_policy" "runtime" {
  name        = "${local.name_prefix}-runtime"
  description = "Slice 17.16 Community Cloud Lambda access to private report artifact store."
  policy      = data.aws_iam_policy_document.runtime_policy.json
  tags        = local.common_tags
}
