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
  description = "Deployment environment label. Slice 8.1 supports production only."
  type        = string

  validation {
    condition     = var.environment_name == "production"
    error_message = "environment_name must be production in this slice."
  }
}

variable "aws_region" {
  description = "AWS region for the data lake bucket."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must look like an AWS region identifier."
  }
}

variable "accepted_retention_days" {
  description = "Retention (days) for accepted objects under raw/ before expiration. Default is review-required, not a validated production policy."
  type        = number
  default     = 365

  validation {
    condition     = var.accepted_retention_days >= 30 && var.accepted_retention_days <= 2555
    error_message = "accepted_retention_days must be between 30 and 2555 days."
  }
}

variable "quarantine_retention_days" {
  description = "Retention (days) for quarantined objects under quarantine/ before expiration. Default is review-required, not a validated production policy. Must be less than or equal to accepted_retention_days (enforced in validation.tf)."
  type        = number
  default     = 90

  validation {
    condition     = var.quarantine_retention_days >= 7 && var.quarantine_retention_days <= 365
    error_message = "quarantine_retention_days must be between 7 and 365 days."
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
  description = "Days after which noncurrent object versions expire."
  type        = number
  default     = 30

  validation {
    condition     = var.noncurrent_version_expiration_days >= 1 && var.noncurrent_version_expiration_days <= 2555
    error_message = "noncurrent_version_expiration_days must be between 1 and 2555 days."
  }
}

variable "encryption_mode" {
  description = "Server-side encryption mode. Only sse_s3 (SSE-S3/AES256) is supported in this slice; SSE-KMS with a customer-managed key is a documented future migration, not created here."
  type        = string
  default     = "sse_s3"

  validation {
    condition     = var.encryption_mode == "sse_s3"
    error_message = "encryption_mode must be sse_s3 in this slice."
  }
}

variable "enable_ingestion_wire" {
  description = "Whether the data lake bucket is wired into any ingestion path (Lambda, EventBridge, etc.). This slice creates bucket foundation only, so this must remain false."
  type        = bool
  default     = false

  validation {
    condition     = var.enable_ingestion_wire == false
    error_message = "enable_ingestion_wire must remain false; this slice provides bucket foundation only, with no ingestion wiring."
  }
}

variable "force_destroy" {
  description = "Whether to allow bucket deletion while objects are present. Defaults to false to avoid accidental data loss."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional resource tags."
  type        = map(string)
  default     = {}
}
