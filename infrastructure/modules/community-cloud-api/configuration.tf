locals {
  lambda_environment = merge(
    {
      CODESTRATA_DEPLOYMENT_MODE        = var.deployment_mode
      CODESTRATA_COMMUNITY_API_VERSION  = "1.0"
      CODESTRATA_AUTHENTICATION_ENABLED = "true"
      CODESTRATA_RATE_LIMIT_ENABLED     = "true"
      CODESTRATA_INGESTION_ENABLED      = var.enable_ingestion ? "true" : "false"
      CODESTRATA_AUTHENTICATION_MODE    = var.authentication_mode
      CODESTRATA_RATE_LIMIT_MODE        = var.rate_limit_mode
    },
    var.insights_secrets_backend == "aws" ? {
      CODESTRATA_INSIGHTS_SECRETS_BACKEND    = "aws"
      CODESTRATA_INSIGHTS_PASSWORD_SECRET_ID = var.insights_password_secret_id
      CODESTRATA_INSIGHTS_SESSION_SECRET_ID  = var.insights_session_secret_id
    } : {},
    var.enable_ingestion ? {
      CODESTRATA_INGESTION_WIRE                  = var.ingestion_wire ? "true" : "false"
      CODESTRATA_DATA_LAKE_ADAPTER               = var.ingestion_wire ? "s3" : "unavailable"
      CODESTRATA_DATA_LAKE_BUCKET                = var.data_lake_bucket_name
      CODESTRATA_COMMUNITY_CREDENTIALS_SECRET_ID = var.community_credentials_secret_id
    } : {},
    var.report_artifacts_bucket_name != "" ? {
      CODESTRATA_REPORT_ARTIFACTS_BUCKET = var.report_artifacts_bucket_name
      CODESTRATA_REPORT_PUBLISHING       = "true"
    } : {}
  )
  # No secret VALUES. Identifiers and feature flags only.
}