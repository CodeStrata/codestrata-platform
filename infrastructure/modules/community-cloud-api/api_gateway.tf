resource "aws_apigatewayv2_api" "community_cloud" {
  name          = local.api_name
  protocol_type = "HTTP"
  description   = "CodeStrata Community Cloud HTTP API (production foundation). One Lambda proxy for all application routes."

  # No CORS configuration in this slice.
  # No OpenAPI docs exposure at the gateway.

  tags = local.common_tags
}

resource "aws_apigatewayv2_integration" "lambda_proxy" {
  api_id                 = aws_apigatewayv2_api.community_cloud.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.community_cloud.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = var.lambda_timeout_seconds * 1000
}

# Catch-all proxy — application RouteRegistry owns the six production routes.
# Infrastructure does not duplicate business route definitions.
resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.community_cloud.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_proxy.id}"
}

resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.community_cloud.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_proxy.id}"
}

resource "aws_apigatewayv2_stage" "production" {
  api_id      = aws_apigatewayv2_api.community_cloud.id
  name        = var.api_stage_name
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = var.api_throttle_burst_limit
    throttling_rate_limit  = var.api_throttle_rate_limit
  }

  tags = local.common_tags
}

resource "aws_lambda_permission" "apigw_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.community_cloud.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.community_cloud.execution_arn}/*/*"
}
