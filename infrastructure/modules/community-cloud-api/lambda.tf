resource "aws_lambda_function" "community_cloud" {
  function_name = local.lambda_function_name
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"
  image_uri     = var.lambda_image_uri
  architectures = [var.lambda_architecture]
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout_seconds

  # No VPC attachment — foundation has no private dependency requiring VPC.
  # No ephemeral business state; /tmp is not used for event persistence.

  environment {
    variables = local.lambda_environment
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy.lambda_logging,
  ]

  tags = local.common_tags
}
