output "lambda_execution_role_name" {
  description = "IAM role name assumed by the Community Cloud Lambda."
  value       = aws_iam_role.lambda_execution.name
}

output "lambda_execution_role_arn" {
  description = "IAM role ARN assumed by the Community Cloud Lambda."
  value       = aws_iam_role.lambda_execution.arn
}

output "api_endpoint" {
  description = "Base HTTPS endpoint for the Community Cloud HTTP API."
  value       = aws_apigatewayv2_api.community_cloud.api_endpoint
}

output "health_endpoint" {
  description = "Full health URL path under the API endpoint."
  value       = "${aws_apigatewayv2_api.community_cloud.api_endpoint}/api/v1/health"
}

output "lambda_function_name" {
  description = "Deployed Lambda function name."
  value       = aws_lambda_function.community_cloud.function_name
}

output "lambda_function_arn" {
  description = "Deployed Lambda function ARN."
  value       = aws_lambda_function.community_cloud.arn
}

output "api_gateway_id" {
  description = "API Gateway HTTP API identifier."
  value       = aws_apigatewayv2_api.community_cloud.id
}

output "log_group_name" {
  description = "CloudWatch log group name for the Lambda."
  value       = aws_cloudwatch_log_group.lambda.name
}

output "ecr_repository_url" {
  description = "Private ECR repository URL for the API image."
  value       = aws_ecr_repository.community_cloud.repository_url
}

output "deployment_mode" {
  description = "Deployment posture label."
  value       = var.deployment_mode
}

output "public_api_base_url" {
  description = "Public Community API authority (branded hostname when custom domain is enabled)."
  value       = var.enable_api_custom_domain ? "https://${var.api_custom_domain_name}" : aws_apigatewayv2_api.community_cloud.api_endpoint
}

output "api_custom_domain_name" {
  description = "Configured custom domain hostname (empty when disabled)."
  value       = var.enable_api_custom_domain ? var.api_custom_domain_name : ""
}

output "api_custom_domain_target" {
  description = "API Gateway regional domain target for Cloudflare DNS-only CNAME (no account IDs)."
  value = (
    var.enable_api_custom_domain
    ? try(aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].target_domain_name, "")
    : ""
  )
}

output "api_custom_domain_hosted_zone_id" {
  description = "API Gateway regional hosted zone id for alias records (optional)."
  value = (
    var.enable_api_custom_domain
    ? try(aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].hosted_zone_id, "")
    : ""
  )
}

output "acm_validation_records" {
  description = "DNS validation CNAMEs for ACM (name/type/value only; no secrets)."
  value = var.enable_api_custom_domain ? [
    for dvo in aws_acm_certificate.api_custom_domain[0].domain_validation_options : {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  ] : []
}

output "execute_api_endpoint_retained" {
  description = "Default execute-api endpoint remains available as FALLBACK_IMPLEMENTATION_ENDPOINT."
  value       = true
}
