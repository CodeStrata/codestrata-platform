resource "aws_cloudwatch_log_group" "lambda" {
  name              = local.log_group_name
  retention_in_days = var.log_retention_days

  # Default AWS-managed encryption for CloudWatch Logs.
  # Application logs must remain structured and privacy-safe (no bodies,
  # Authorization headers, raw IPs, event IDs, source paths, or prompts).

  tags = local.common_tags
}
