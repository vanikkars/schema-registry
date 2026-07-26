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

# S3 Bucket for Iceberg Tables
resource "aws_s3_bucket" "iceberg_data" {
  bucket = "iceberg-data-${data.aws_caller_identity.current.account_id}-${var.aws_region}"

  tags = merge(
    var.common_tags,
    {
      Name = "iceberg-data-bucket"
    }
  )
}

# Enable versioning for data protection
resource "aws_s3_bucket_versioning" "iceberg_data" {
  bucket = aws_s3_bucket.iceberg_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "iceberg_data" {
  bucket = aws_s3_bucket.iceberg_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "iceberg_data" {
  bucket = aws_s3_bucket.iceberg_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# AWS Glue Database for Iceberg Tables
resource "aws_glue_catalog_database" "iceberg_db" {
  name        = "iceberg_tables"
  description = "Database for Iceberg tables created from data contracts"

  tags = merge(
    var.common_tags,
    {
      Name = "iceberg-tables-db"
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

output "iceberg_bucket_name" {
  value       = aws_s3_bucket.iceberg_data.id
  description = "S3 bucket for Iceberg table data"
}

output "iceberg_bucket_arn" {
  value       = aws_s3_bucket.iceberg_data.arn
  description = "ARN of the S3 bucket for Iceberg tables"
}

output "glue_database_name" {
  value       = aws_glue_catalog_database.iceberg_db.name
  description = "Glue database for Iceberg tables"
}
