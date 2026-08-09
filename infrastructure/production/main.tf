module "community_cloud_api" {
  source = "../modules/community-cloud-api"

  project_name                    = var.project_name
  environment_name                = "production"
  aws_region                      = var.aws_region
  lambda_image_uri                = var.lambda_image_uri
  lambda_memory_size              = var.lambda_memory_size
  lambda_timeout_seconds          = var.lambda_timeout_seconds
  lambda_architecture             = var.lambda_architecture
  log_retention_days              = var.log_retention_days
  api_throttle_burst_limit        = var.api_throttle_burst_limit
  api_throttle_rate_limit         = var.api_throttle_rate_limit
  deployment_mode                 = "production_ingestion"
  enable_ingestion                = true
  ingestion_wire                  = true
  data_lake_bucket_name           = module.community_data_lake.bucket_name
  authentication_mode             = "enabled_secrets_manager_verifier"
  rate_limit_mode                 = "api_gateway_plus_process_local"
  insights_secrets_backend        = "aws"
  insights_password_secret_id     = "codestrata/insights/dashboard-password"
  insights_session_secret_id      = "codestrata/insights/session-secret"
  community_credentials_secret_id = "codestrata/community/client-credentials"
  tags                            = var.tags
}
