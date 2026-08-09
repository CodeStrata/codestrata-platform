output "role_name" {
  description = "GitHub production deployment role name (safe identifier)."
  value       = aws_iam_role.github_production.name
}

output "oidc_provider_url" {
  description = "Canonical GitHub Actions OIDC issuer URL (HTTPS). Deterministic: do not echo AWS-normalized provider attribute."
  value       = local.oidc_url
}

output "oidc_audience" {
  description = "OIDC audience required by the trust policy."
  value       = local.oidc_audience
}

output "trust_subject" {
  description = "Exact OIDC subject allowed to assume the role."
  value       = local.trust_subject
}

output "remote_state_policy_name" {
  description = "Customer-managed policy attached for dedicated state-bucket access."
  value       = aws_iam_policy.remote_state.name
}

output "session_duration_seconds" {
  description = "Maximum role session duration."
  value       = aws_iam_role.github_production.max_session_duration
}

output "state_bucket_name" {
  description = "Dedicated OpenTofu state bucket scoped in the policy."
  value       = var.state_bucket_name
}
