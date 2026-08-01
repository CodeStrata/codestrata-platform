terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_s3_bucket" "validation_stub" {
  bucket = "codestrata-validation-terraform-stub"
}

resource "aws_lambda_function" "validation_stub" {
  function_name = "codestrata-validation-stub"
  role          = "arn:aws:iam::000000000000:role/validation-stub"
  handler       = "handler.main"
  runtime       = "python3.12"
}
