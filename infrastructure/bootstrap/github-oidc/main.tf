locals {
  oidc_url      = "https://token.actions.githubusercontent.com"
  oidc_audience = "sts.amazonaws.com"
  # GitHub Actions OIDC certificate thumbprints (AWS still requires at least one).
  oidc_thumbprints = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd",
  ]
  # Closed set only — never repo:CodeStrata/* .
  trusted_repositories = distinct(concat([var.github_repository], var.github_repositories))
  trust_subjects = [
    for repo in local.trusted_repositories :
    "repo:${repo}:environment:${var.github_environment}"
  ]
  trust_subject = local.trust_subjects[0]
}

data "aws_caller_identity" "current" {}

# GitHub Actions OIDC provider (account-global). Do not duplicate if already present —
# bootstrap script imports when GetOpenIDConnectProvider succeeds.
resource "aws_iam_openid_connect_provider" "github" {
  url             = local.oidc_url
  client_id_list  = [local.oidc_audience]
  thumbprint_list = local.oidc_thumbprints

  tags = {
    Project   = "codestrata"
    Component = "github-oidc"
    Purpose   = "github-actions-sts"
    ManagedBy = "opentofu"
  }
}

data "aws_iam_policy_document" "github_assume" {
  statement {
    sid     = "GitHubActionsAssumeRoleWithWebIdentity"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = [local.oidc_audience]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = local.trust_subjects
    }
  }
}

resource "aws_iam_role" "github_production" {
  name                 = var.role_name
  description          = "CodeStrata GitHub Actions production identity (OIDC). Minimal remote-state access in Slice 17.3."
  assume_role_policy   = data.aws_iam_policy_document.github_assume.json
  max_session_duration = var.session_duration_seconds

  tags = {
    Project     = "codestrata"
    Component   = "github-oidc"
    Environment = "production"
    Purpose     = "ci-cd-oidc-only"
    ManagedBy   = "opentofu"
  }
}

data "aws_iam_policy_document" "remote_state" {
  statement {
    sid    = "ListStateBucket"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [
      "arn:aws:s3:::${var.state_bucket_name}",
    ]
  }

  statement {
    sid    = "StateObjectAndNativeLockfile"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObjectVersion",
    ]
    resources = [
      "arn:aws:s3:::${var.state_bucket_name}/${var.state_key_prefix}*",
    ]
  }
}

resource "aws_iam_policy" "remote_state" {
  name        = var.remote_state_policy_name
  description = "CodeStrata GitHub OIDC role: dedicated OpenTofu remote-state S3 access only (native lockfile)."
  policy      = data.aws_iam_policy_document.remote_state.json

  tags = {
    Project   = "codestrata"
    Component = "github-oidc"
    Purpose   = "remote-state-access"
    ManagedBy = "opentofu"
  }
}

resource "aws_iam_role_policy_attachment" "remote_state" {
  role       = aws_iam_role.github_production.name
  policy_arn = aws_iam_policy.remote_state.arn
}
