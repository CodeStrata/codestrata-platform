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
