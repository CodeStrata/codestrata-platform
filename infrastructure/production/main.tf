module "community_cloud_api" {
  source = "../modules/community-cloud-api"

  project_name             = var.project_name
  environment_name         = "production"
  aws_region               = var.aws_region
  lambda_image_uri         = var.lambda_image_uri
  lambda_memory_size       = var.lambda_memory_size
  lambda_timeout_seconds   = var.lambda_timeout_seconds
  lambda_architecture      = var.lambda_architecture
  log_retention_days       = var.log_retention_days
  api_throttle_burst_limit = var.api_throttle_burst_limit
  api_throttle_rate_limit  = var.api_throttle_rate_limit
  deployment_mode          = "production_foundation"
  enable_ingestion         = false
  authentication_mode      = "enabled_verifier_unavailable"
  rate_limit_mode          = "api_gateway_plus_process_local"
  tags                     = var.tags
}
