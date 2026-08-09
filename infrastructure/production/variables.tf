variable "project_name" {
  type    = string
  default = "codestrata"
}

variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "lambda_image_uri" {
  description = "Container image URI (immutable tag or digest). Placeholder only in examples."
  type        = string
}

variable "lambda_memory_size" {
  type    = number
  default = 512
}

variable "lambda_timeout_seconds" {
  type    = number
  default = 30
}

variable "lambda_architecture" {
  type    = string
  default = "arm64"
}

variable "log_retention_days" {
  type    = number
  default = 30
}

variable "api_throttle_burst_limit" {
  type    = number
  default = 50
}

variable "api_throttle_rate_limit" {
  type    = number
  default = 25
}

variable "tags" {
  type    = map(string)
  default = {}
}
