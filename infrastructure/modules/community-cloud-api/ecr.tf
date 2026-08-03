resource "aws_ecr_repository" "community_cloud" {
  name                 = local.ecr_repository_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  # Private repository — no public access.
  force_delete = false

  tags = local.common_tags
}

resource "aws_ecr_lifecycle_policy" "community_cloud" {
  repository = aws_ecr_repository.community_cloud.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Retain a bounded number of images; expire untagged leftovers."
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 14
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep the newest tagged images; expire older tags."
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 20
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
