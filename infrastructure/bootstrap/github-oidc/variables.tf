variable "aws_region" {
  type        = string
  description = "AWS region for IAM identity resources (global IAM; region used for provider)."
  default     = "us-west-2"
}

variable "github_repository" {
  type        = string
  description = "Primary GitHub repository in owner/name form trusted for OIDC (legacy single-value)."
  default     = "CodeStrata/codestrata-platform"
}

variable "github_repositories" {
  type        = list(string)
  description = "Explicit GitHub repositories trusted for OIDC (no org wildcards). Transitional dual-trust during infrastructure cutover."
  default = [
    "CodeStrata/codestrata-platform",
    "CodeStrata/codestrata-infrastructure",
  ]
}

variable "github_environment" {
  type        = string
  description = "Protected GitHub environment name required in the OIDC subject."
  default     = "production"
}

variable "role_name" {
  type        = string
  description = "IAM role name assumed by GitHub Actions via OIDC."
  default     = "codestrata-github-actions-production"
}

variable "remote_state_policy_name" {
  type        = string
  description = "Customer-managed IAM policy name for dedicated OpenTofu state access."
  default     = "CodeStrataGitHubRemoteStateAccess"
}

variable "state_bucket_name" {
  type        = string
  description = "Dedicated OpenTofu remote-state S3 bucket name."
}

variable "state_key_prefix" {
  type        = string
  description = "State/lock object prefix inside the state bucket."
  default     = "codestrata/community-cloud/production/"
}

variable "session_duration_seconds" {
  type        = number
  description = "Maximum OIDC role session duration."
  default     = 3600
}
