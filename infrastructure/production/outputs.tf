output "api_base_url" {
  description = "Implementation execute-api base URL (FALLBACK; not public authority)."
  value       = module.community_cloud_api.api_endpoint
}

output "public_api_base_url" {
  description = "Public Community API authority (https://api.codestrata.ai)."
  value       = module.community_cloud_api.public_api_base_url
}

output "api_custom_domain_name" {
  value = module.community_cloud_api.api_custom_domain_name
}

output "api_custom_domain_target" {
  description = "Cloudflare DNS-only CNAME target for api.codestrata.ai."
  value       = module.community_cloud_api.api_custom_domain_target
}

output "acm_validation_records" {
  description = "ACM DNS validation records (safe name/type/value)."
  value       = module.community_cloud_api.acm_validation_records
}

output "health_url" {
  description = "Health check URL on the public API authority when domain is live."
  value       = "${module.community_cloud_api.public_api_base_url}/api/v1/health"
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

output "data_lake_bucket_name" {
  value = module.community_data_lake.bucket_name
}

output "data_lake_writer_policy_arn" {
  value = module.community_data_lake.writer_policy_arn
}

output "report_artifacts_bucket_name" {
  description = "Private Community report artifact store (not Data Lake)."
  value       = module.community_report_artifacts.bucket_name
}

output "report_artifacts_runtime_policy_arn" {
  value = module.community_report_artifacts.runtime_policy_arn
}

output "public_reports_base_url" {
  description = "Public branded report URL authority."
  value       = "https://reports.codestrata.ai"
}
