data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    sid     = "AllowLambdaAssume"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_execution" {
  name               = "${local.name_prefix}-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "lambda_logging" {
  statement {
    sid    = "CloudWatchLogGroup"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "${aws_cloudwatch_log_group.lambda.arn}:*",
    ]
  }
}

data "aws_iam_policy_document" "lambda_ecr_pull" {
  statement {
    sid    = "EcrPullImage"
    effect = "Allow"
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability",
    ]
    resources = [
      aws_ecr_repository.community_cloud.arn,
    ]
  }

  # AWS requires Resource="*" for ecr:GetAuthorizationToken (documented exception).
  statement {
    sid    = "EcrAuthorizationToken"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "lambda_logging" {
  name   = "${local.name_prefix}-lambda-logging"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_logging.json
}

resource "aws_iam_role_policy" "lambda_ecr_pull" {
  name   = "${local.name_prefix}-lambda-ecr"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_ecr_pull.json
}

# No S3 / DynamoDB / SQS / Secrets Manager / Parameter Store permissions.
