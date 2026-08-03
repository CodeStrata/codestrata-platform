locals {
  lambda_environment = {
    CODESTRATA_DEPLOYMENT_MODE         = var.deployment_mode
    CODESTRATA_COMMUNITY_API_VERSION   = "1.0"
    CODESTRATA_AUTHENTICATION_ENABLED  = "true"
    CODESTRATA_RATE_LIMIT_ENABLED      = "true"
    CODESTRATA_INGESTION_ENABLED       = var.enable_ingestion ? "true" : "false"
    CODESTRATA_AUTHENTICATION_MODE     = var.authentication_mode
    CODESTRATA_RATE_LIMIT_MODE         = var.rate_limit_mode
    # No secrets. No verifier credentials. No sink endpoints.
  }
}
