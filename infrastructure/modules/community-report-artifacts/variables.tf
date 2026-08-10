variable "project_name" {
  description = "Short project name used in resource naming."
  type        = string
  default     = "codestrata"

  validation {
    condition     = can(regex("^[a-z0-9-]{2,32}$", var.project_name))
    error_message = "project_name must be 2-32 lowercase alphanumeric characters or hyphens."
  }
}

variable "environment_name" {
  description = "Deployment environment label. Slice 17.16 supports production only."
  type        = string

  validation {
    condition     = var.environment_name == "production"
    error_message = "environment_name must be production in this slice."
  }
}

variable "aws_region" {
  description = "AWS region for the report artifact bucket."
  type        = string
  default     = "us-west-2"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must look like an AWS region identifier."
  }
}

variable "incomplete_multipart_days" {
  description = "Days after which incomplete multipart uploads are aborted bucket-wide."
  type        = number
  default     = 7

  validation {
    condition     = var.incomplete_multipart_days >= 1 && var.incomplete_multipart_days <= 90
    error_message = "incomplete_multipart_days must be between 1 and 90 days."
  }
}

variable "noncurrent_version_expiration_days" {
  description = "Days after which noncurrent object versions expire (ops recovery only; not product history)."
  type        = number
  default     = 30

  validation {
    condition     = var.noncurrent_version_expiration_days >= 1 && var.noncurrent_version_expiration_days <= 2555
    error_message = "noncurrent_version_expiration_days must be between 1 and 2555 days."
  }
}

variable "staging_expiration_days" {
  description = "Days before abandoned staging prefixes expire."
  type        = number
  default     = 2

  validation {
    condition     = var.staging_expiration_days >= 1 && var.staging_expiration_days <= 14
    error_message = "staging_expiration_days must be between 1 and 14 days."
  }
}

variable "encryption_mode" {
  description = "Server-side encryption mode. Only sse_s3 (SSE-S3/AES256) is supported in this slice."
  type        = string
  default     = "sse_s3"

  validation {
    condition     = var.encryption_mode == "sse_s3"
    error_message = "encryption_mode must be sse_s3 in this slice."
  }
}

variable "force_destroy" {
  description = "Whether to allow bucket deletion while objects are present."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional resource tags."
  type        = map(string)
  default     = {}
}
