module "community_data_lake" {
  source = "../modules/community-data-lake"

  project_name          = var.project_name
  environment_name      = "production"
  aws_region            = var.aws_region
  enable_ingestion_wire = false
  tags                  = var.tags
}
