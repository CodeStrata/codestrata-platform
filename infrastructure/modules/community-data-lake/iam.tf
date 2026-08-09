# Least-privilege S3 writer policy for future producers of Community Data
# Lake objects. This document is NOT attached to any IAM role or Lambda in
# this slice — ingestion wiring is deferred until enable_ingestion_wire is
# intentionally turned on in a later slice. No aws_iam_role is created here.
#
# Slice 8.12: statement SIDs are stable and descriptive; accepted and
# quarantine GetObject permissions are separate for auditability; delete is
# explicitly Denied on both prefixes (lifecycle expiration is S3-service
# behavior and is not blocked by this identity-policy Deny).

data "aws_iam_policy_document" "writer_policy" {
  statement {
    sid    = "WriteAcceptedRawObjects"
    effect = "Allow"

    actions = [
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.community_data_lake.arn}/${local.accepted_prefix}*",
    ]
  }

  statement {
    sid    = "WriteQuarantineRecords"
    effect = "Allow"

    actions = [
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.community_data_lake.arn}/${local.quarantine_prefix}*",
    ]
  }

  # HeadObject requires s3:GetObject on the object ARN (there is no IAM
  # action named s3:HeadObject). Used only for exact-retry / conflict
  # classification after IfNoneMatch PreconditionFailed.
  statement {
    sid    = "VerifyAcceptedRawObjects"
    effect = "Allow"

    actions = [
      "s3:GetObject",
    ]

    resources = [
      "${aws_s3_bucket.community_data_lake.arn}/${local.accepted_prefix}*",
    ]
  }

  statement {
    sid    = "VerifyQuarantineRecords"
    effect = "Allow"

    actions = [
      "s3:GetObject",
    ]

    resources = [
      "${aws_s3_bucket.community_data_lake.arn}/${local.quarantine_prefix}*",
    ]
  }

  statement {
    sid    = "WriteIdentityObjects"
    effect = "Allow"

    actions = [
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.community_data_lake.arn}/identity/*",
    ]
  }

  statement {
    sid    = "VerifyIdentityObjects"
    effect = "Allow"

    actions = [
      "s3:GetObject",
    ]

    resources = [
      "${aws_s3_bucket.community_data_lake.arn}/identity/*",
    ]
  }

  # S3 returns 403 (not 404) for GetObject on a missing key when the caller
  # lacks ListBucket. Identity + immutable writes use GetObject for miss
  # detection; scope ListBucket to approved prefixes only.
  statement {
    sid    = "ListApprovedWriterPrefixes"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.community_data_lake.arn,
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "${local.accepted_prefix}",
        "${local.accepted_prefix}*",
        "${local.quarantine_prefix}",
        "${local.quarantine_prefix}*",
        "identity/",
        "identity/*",
      ]
    }
  }

  statement {
    sid    = "DenyIdentityObjectDeletion"
    effect = "Deny"

    actions = [
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
    ]

    resources = [
      "${aws_s3_bucket.community_data_lake.arn}/identity/*",
    ]
  }

  # ListBucket is required for correct missing-object detection on GetObject
  # (without it S3 returns 403 instead of 404). Scope is prefix-conditioned
  # above — never grant unconditional ListBucket or cross-bucket list.

  statement {
    sid    = "DenyAcceptedObjectDeletion"
    effect = "Deny"

    actions = [
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
    ]

    resources = [
      "${aws_s3_bucket.community_data_lake.arn}/${local.accepted_prefix}*",
    ]
  }

  statement {
    sid    = "DenyQuarantineObjectDeletion"
    effect = "Deny"

    actions = [
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
    ]

    resources = [
      "${aws_s3_bucket.community_data_lake.arn}/${local.quarantine_prefix}*",
    ]
  }
}

# Standalone policy resource for future attachment. Not attached to any
# role, user, or Lambda in this slice.
resource "aws_iam_policy" "writer" {
  name        = "${local.name_prefix}-writer"
  description = "Least-privilege S3 writer policy for the Community Data Lake bucket. Not attached to any role in this slice."
  policy      = data.aws_iam_policy_document.writer_policy.json

  tags = local.common_tags
}

# No aws_iam_role, no role/policy attachment, no ListAllMyBuckets, no KMS
# actions, and no S3 admin wildcard (Resource = "*") anywhere in this
# document.
