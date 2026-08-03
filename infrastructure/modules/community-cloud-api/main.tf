locals {
  name_prefix = "${var.project_name}-community-cloud-${var.environment_name}"

  lambda_function_name = coalesce(
    var.lambda_function_name != "" ? var.lambda_function_name : null,
    "${local.name_prefix}-api"
  )

  api_name = coalesce(
    var.api_name != "" ? var.api_name : null,
    "${local.name_prefix}-http"
  )

  ecr_repository_name = coalesce(
    var.ecr_repository_name != "" ? var.ecr_repository_name : null,
    "${var.project_name}/community-cloud-api"
  )

  log_group_name = "/aws/lambda/${local.lambda_function_name}"

  common_tags = merge(
    {
      Project         = var.project_name
      Environment     = var.environment_name
      Component       = "community-cloud-api"
      DeploymentMode  = var.deployment_mode
      ManagedBy       = "opentofu"
      Ownership       = "platform-private"
    },
    var.tags
  )
}
