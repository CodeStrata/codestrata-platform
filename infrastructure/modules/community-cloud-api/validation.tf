check "production_posture" {
  assert {
    condition = contains(
      ["enabled_verifier_unavailable", "enabled_secrets_manager_verifier"],
      var.authentication_mode
    )
    error_message = "authentication_mode must keep authentication enabled."
  }

  assert {
    condition = contains(
      ["production_foundation", "production_ingestion"],
      var.deployment_mode
    )
    error_message = "deployment_mode must be production_foundation or production_ingestion."
  }

  assert {
    condition     = !(var.enable_ingestion && var.deployment_mode == "production_foundation")
    error_message = "enable_ingestion=true requires deployment_mode=production_ingestion."
  }
}
