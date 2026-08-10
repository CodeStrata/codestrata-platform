# Slice 17.16 — dedicated private report artifact store (not Data Lake).

module "community_report_artifacts" {
  source = "../modules/community-report-artifacts"

  project_name     = var.project_name
  environment_name = "production"
  aws_region       = var.aws_region
  tags             = var.tags
}
