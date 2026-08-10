# Slice 17.6 — Runtime security IAM (secret-free).
#
# Creates/attaches Insights Data Lake reader + Secrets Manager read policies
# on the Community Cloud Lambda execution role.
#
# Does NOT:
# - store secret VALUES (operational script only)
# - attach Data Lake writer (deferred to Slice 17.7 / enable_ingestion_wire)
# - enable production ingestion
# - grant Bedrock / provider credentials / DynamoDB / Athena / Glue / RDS / Redis
# - grant PutObject or DeleteObject on the lake
# - grant GetObject outside raw/*

data "aws_caller_identity" "runtime_security" {}
data "aws_region" "runtime_security" {}

locals {
  runtime_password_secret_id           = "codestrata/insights/dashboard-password"
  runtime_session_secret_id            = "codestrata/insights/session-secret"
  runtime_insights_reader_policy_name  = "codestrata-community-insights-production-reader"
  runtime_insights_secrets_policy_name = "codestrata-community-insights-production-secrets"
  runtime_lambda_role_name             = "codestrata-community-cloud-production-lambda"
  runtime_data_lake_bucket             = module.community_data_lake.bucket_name
  runtime_data_lake_arn                = module.community_data_lake.bucket_arn
  runtime_account_id                   = data.aws_caller_identity.runtime_security.account_id
  runtime_region                       = data.aws_region.runtime_security.id
}

data "aws_iam_policy_document" "insights_production_reader" {
  statement {
    sid    = "ListRawAnalyticsPrefixes"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      local.runtime_data_lake_arn,
    ]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "raw/",
        "raw/*",
      ]
    }
  }

  statement {
    sid    = "GetRawAnalyticsObjects"
    effect = "Allow"
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${local.runtime_data_lake_arn}/raw/*",
    ]
  }
}

resource "aws_iam_policy" "insights_production_reader" {
  name        = local.runtime_insights_reader_policy_name
  description = "Slice 17.6 bounded Insights S3 read on Community Data Lake raw/* only."
  policy      = data.aws_iam_policy_document.insights_production_reader.json

  tags = merge(var.tags, {
    Project     = var.project_name
    Environment = "production"
    Component   = "community-insights-runtime"
    Slice       = "17.6"
    ManagedBy   = "opentofu"
  })
}

data "aws_iam_policy_document" "insights_production_secrets" {
  statement {
    sid    = "InsightsAuthGetSecretValue"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      "arn:aws:secretsmanager:${local.runtime_region}:${local.runtime_account_id}:secret:${local.runtime_password_secret_id}-*",
      "arn:aws:secretsmanager:${local.runtime_region}:${local.runtime_account_id}:secret:${local.runtime_session_secret_id}-*",
    ]
  }
}

resource "aws_iam_policy" "insights_production_secrets" {
  name        = local.runtime_insights_secrets_policy_name
  description = "Slice 17.6 GetSecretValue only for Insights auth secrets."
  policy      = data.aws_iam_policy_document.insights_production_secrets.json

  tags = merge(var.tags, {
    Project     = var.project_name
    Environment = "production"
    Component   = "community-insights-runtime"
    Slice       = "17.6"
    ManagedBy   = "opentofu"
  })
}

resource "aws_iam_role_policy_attachment" "lambda_insights_reader" {
  role       = local.runtime_lambda_role_name
  policy_arn = aws_iam_policy.insights_production_reader.arn
}

resource "aws_iam_role_policy_attachment" "lambda_insights_secrets" {
  role       = local.runtime_lambda_role_name
  policy_arn = aws_iam_policy.insights_production_secrets.arn
}

# Slice 17.7: attach Data Lake writer for production ingestion (raw/quarantine/identity).
resource "aws_iam_role_policy_attachment" "lambda_data_lake_writer" {
  role       = local.runtime_lambda_role_name
  policy_arn = module.community_data_lake.writer_policy_arn
}

# Slice 17.16: private report artifact store (separate from Data Lake).
resource "aws_iam_role_policy_attachment" "lambda_report_artifacts" {
  role       = local.runtime_lambda_role_name
  policy_arn = module.community_report_artifacts.runtime_policy_arn
}