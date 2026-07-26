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

# Schema for User data contract
resource "aws_glue_schema" "user_schema" {
  registry_arn       = aws_glue_registry.schema_registry.arn
  schema_name        = "user-schema"
  data_format        = "AVRO"
  compatibility      = "BACKWARD"
  description        = "Schema for user records"

  schema_definition = jsonencode({
    type      = "record"
    name      = "User"
    namespace = "com.example.schema"
    fields = [
      {
        name = "user_name"
        type = "string"
      },
      {
        name = "email"
        type = "string"
      },
      {
        name = "date_of_birth"
        type = "string"
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name = "user-schema"
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

output "user_schema_arn" {
  value       = aws_glue_schema.user_schema.arn
  description = "ARN of the User schema"
}

output "user_schema_name" {
  value       = aws_glue_schema.user_schema.schema_name
  description = "Name of the User schema"
}