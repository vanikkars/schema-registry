terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# AWS Glue Registry
# Note: Schemas are created via Python API (upload_to_glue.py) instead of Terraform
# This provides more flexibility and keeps infrastructure and data contracts separate
resource "aws_glue_registry" "schema_registry" {
  registry_name = var.registry_name
  description   = var.registry_description

  tags = merge(
    var.common_tags,
    {
      Name = var.registry_name
    }
  )
}

# Output the schema registry ARN and details
output "schema_registry_arn" {
  value       = aws_glue_registry.schema_registry.arn
  description = "ARN of the Glue Schema Registry"
}

output "schema_registry_name" {
  value       = aws_glue_registry.schema_registry.registry_name
  description = "Name of the Glue Schema Registry"
}
