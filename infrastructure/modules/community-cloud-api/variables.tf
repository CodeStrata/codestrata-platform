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
  description = "Deployment environment label. Slice 7.14 supports production only."
  type        = string

  validation {
    condition     = var.environment_name == "production"
    error_message = "environment_name must be production in this slice."
  }
}

variable "aws_region" {
  description = "AWS region for API resources."
  type        = string
  default     = "us-west-2"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must look like an AWS region identifier."
  }
}

variable "lambda_function_name" {
  description = "Lambda function name. Empty selects a deterministic default."
  type        = string
  default     = ""
}

variable "lambda_memory_size" {
  description = "Lambda memory in MB."
  type        = number
  default     = 512

  validation {
    condition     = var.lambda_memory_size >= 256 && var.lambda_memory_size <= 3008
    error_message = "lambda_memory_size must be between 256 and 3008."
  }
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 30

  validation {
    condition     = var.lambda_timeout_seconds >= 5 && var.lambda_timeout_seconds <= 60
    error_message = "lambda_timeout_seconds must be between 5 and 60 for this foundation."
  }
}

variable "lambda_architecture" {
  description = "Lambda instruction set architecture."
  type        = string
  default     = "arm64"

  validation {
    condition     = contains(["arm64", "x86_64"], var.lambda_architecture)
    error_message = "lambda_architecture must be arm64 or x86_64."
  }
}

variable "lambda_image_uri" {
  description = "Container image URI (repository:tag or digest) for the Lambda."
  type        = string

  validation {
    condition     = length(var.lambda_image_uri) > 0
    error_message = "lambda_image_uri is required."
  }
}

variable "api_name" {
  description = "API Gateway HTTP API name. Empty selects a deterministic default."
  type        = string
  default     = ""
}

variable "api_stage_name" {
  description = "API Gateway stage name."
  type        = string
  default     = "$default"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 30

  validation {
    condition = contains(
      [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653],
      var.log_retention_days
    )
    error_message = "log_retention_days must be a CloudWatch-supported retention value."
  }
}

variable "authentication_mode" {
  description = "Application authentication mode."
  type        = string
  default     = "enabled_verifier_unavailable"

  validation {
    condition = contains(
      ["enabled_verifier_unavailable", "enabled_secrets_manager_verifier"],
      var.authentication_mode
    )
    error_message = "authentication_mode must keep authentication enabled."
  }
}

variable "rate_limit_mode" {
  description = "Rate-limit deployment mode."
  type        = string
  default     = "api_gateway_plus_process_local"

  validation {
    condition     = contains(["api_gateway_plus_process_local"], var.rate_limit_mode)
    error_message = "rate_limit_mode must be api_gateway_plus_process_local in this slice."
  }
}

variable "deployment_mode" {
  description = "Deployment posture label exposed to the runtime."
  type        = string
  default     = "production_foundation"

  validation {
    condition = contains(
      ["production_foundation", "production_ingestion"],
      var.deployment_mode
    )
    error_message = "deployment_mode must be production_foundation or production_ingestion."
  }
}

variable "enable_ingestion" {
  description = "Whether durable production ingestion is enabled (Slice 17.7+). Requires sinks, verifier, and writer attachment."
  type        = bool
  default     = false
}

variable "api_throttle_burst_limit" {
  description = "API Gateway stage burst limit (outer protection)."
  type        = number
  default     = 50

  validation {
    condition     = var.api_throttle_burst_limit >= 1 && var.api_throttle_burst_limit <= 5000
    error_message = "api_throttle_burst_limit out of allowed bounds."
  }
}

variable "api_throttle_rate_limit" {
  description = "API Gateway stage steady-state rate limit (requests/second)."
  type        = number
  default     = 25

  validation {
    condition     = var.api_throttle_rate_limit >= 1 && var.api_throttle_rate_limit <= 5000
    error_message = "api_throttle_rate_limit out of allowed bounds."
  }
}

variable "ecr_repository_name" {
  description = "ECR repository name. Empty selects a deterministic default."
  type        = string
  default     = ""
}

variable "insights_secrets_backend" {
  description = "Insights secrets port backend. aws enables Secrets Manager reads (identifiers only in env)."
  type        = string
  default     = "unavailable"

  validation {
    condition     = contains(["unavailable", "aws"], var.insights_secrets_backend)
    error_message = "insights_secrets_backend must be unavailable or aws."
  }
}

variable "insights_password_secret_id" {
  description = "Secrets Manager secret name for dashboard password verifier (value out of band)."
  type        = string
  default     = "codestrata/insights/dashboard-password"
}

variable "insights_session_secret_id" {
  description = "Secrets Manager secret name for session signing material (value out of band)."
  type        = string
  default     = "codestrata/insights/session-secret"
}

variable "data_lake_bucket_name" {
  description = "Community Data Lake bucket name for production ingestion wiring (empty when disabled)."
  type        = string
  default     = ""
}

variable "report_artifacts_bucket_name" {
  description = "Private report artifact bucket for Slice 17.16 publishing (empty when disabled)."
  type        = string
  default     = ""
}

variable "ingestion_wire" {
  description = "Second hard gate for Data Lake adapter wiring (Slice 17.7)."
  type        = bool
  default     = false
}

variable "community_credentials_secret_id" {
  description = "Secrets Manager secret name for Community client credential fingerprints (values out of band)."
  type        = string
  default     = "codestrata/community/client-credentials"
}

variable "enable_api_custom_domain" {
  description = "Slice 17.14 — provision ACM + API Gateway custom domain for api.codestrata.ai."
  type        = bool
  default     = true
}

variable "api_custom_domain_name" {
  description = "Public Community API hostname (exact; no wildcard)."
  type        = string
  default     = "api.codestrata.ai"

  validation {
    condition     = can(regex("^[a-z0-9.-]+\\.[a-z]{2,}$", var.api_custom_domain_name))
    error_message = "api_custom_domain_name must be a lowercase DNS hostname."
  }
}

variable "tags" {
  description = "Additional resource tags."
  type        = map(string)
  default     = {}
}
