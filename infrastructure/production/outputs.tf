output "api_base_url" {
  description = "Base HTTPS URL for the Community Cloud API."
  value       = module.community_cloud_api.api_endpoint
}

output "health_url" {
  description = "Health check URL."
  value       = module.community_cloud_api.health_endpoint
}

output "lambda_function_name" {
  value = module.community_cloud_api.lambda_function_name
}

output "lambda_function_arn" {
  value = module.community_cloud_api.lambda_function_arn
}

output "api_gateway_id" {
  value = module.community_cloud_api.api_gateway_id
}

output "ecr_repository_url" {
  value = module.community_cloud_api.ecr_repository_url
}

output "cloudwatch_log_group" {
  value = module.community_cloud_api.log_group_name
}

output "deployment_mode" {
  value = module.community_cloud_api.deployment_mode
}
