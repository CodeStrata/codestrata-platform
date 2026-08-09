variable "aws_region" {
  type        = string
  description = "AWS region for the OpenTofu remote-state bucket."
  default     = "us-west-2"
}

variable "bucket_name" {
  type        = string
  description = "Globally unique S3 bucket name for OpenTofu remote state (created by bootstrap script)."
}
