# Community Insights auth infrastructure contracts (Slice 15.9)
#
# Source-controlled references only. Do NOT put secret VALUES here.
# Owners create Secrets Manager entries outside Git during deployment.
# This module is not applied in Slice 15.9 (production_deployment_enabled=false).

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

variable "password_secret_id" {
  type        = string
  description = "Secrets Manager secret name/ARN for dashboard password verifier (value out of band)."
  default     = "codestrata/insights/dashboard-password"
}

variable "session_secret_id" {
  type        = string
  description = "Secrets Manager secret name/ARN for session HMAC signing key (value out of band)."
  default     = "codestrata/insights/session-secret"
}

variable "auth_lambda_role_name" {
  type        = string
  description = "IAM role name for Insights auth runtime (GetSecretValue only on listed secrets)."
  default     = "codestrata-insights-auth-runtime"
}

variable "enable_module" {
  type        = bool
  description = "Must remain false until a future deployment slice. Slice 15.9 does not deploy."
  default     = false

  validation {
    condition     = var.enable_module == false
    error_message = "community-insights-auth must not be enabled in Slice 15.9 (no production deployment)."
  }
}

locals {
  secret_ids = [
    var.password_secret_id,
    var.session_secret_id,
  ]
}

# Placeholder IAM document — applied only when a future slice sets enable_module
# and wires real secret ARNs. No secret values. No PutSecretValue for app runtime.
data "aws_iam_policy_document" "insights_auth_secrets_read" {
  statement {
    sid    = "InsightsAuthGetSecretValue"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    # Resource ARNs are environment-specific; keep names as documentation until wired.
    resources = [
      "arn:aws:secretsmanager:*:*:secret:${var.password_secret_id}-*",
      "arn:aws:secretsmanager:*:*:secret:${var.session_secret_id}-*",
    ]
  }
}

output "password_secret_id" {
  value       = var.password_secret_id
  description = "Identifier only — not the password."
}

output "session_secret_id" {
  value       = var.session_secret_id
  description = "Identifier only — not the signing key."
}

output "secrets_read_policy_json" {
  value       = data.aws_iam_policy_document.insights_auth_secrets_read.json
  description = "Least-privilege GetSecretValue policy document for auth runtime."
}

output "frontend_secrets_manager_permissions" {
  value       = []
  description = "Frontend must have zero Secrets Manager permissions."
}

output "production_deployment_enabled" {
  value = false
}
