provider "aws" {
  region = var.aws_region

  # Do not hardcode account IDs, profiles, or credentials.
  # Use standard AWS credential chain / environment configuration.
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "production"
      ManagedBy   = "opentofu"
    }
  }
}
