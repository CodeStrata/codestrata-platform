check "foundation_fail_closed" {
  assert {
    condition     = var.enable_ingestion == false
    error_message = "Ingestion must remain disabled for the production foundation."
  }

  assert {
    condition     = var.authentication_mode == "enabled_verifier_unavailable"
    error_message = "Authentication must stay enabled without a production verifier in this slice."
  }

  assert {
    condition     = var.deployment_mode == "production_foundation"
    error_message = "deployment_mode must remain production_foundation."
  }
}
