variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region where resources will be created"
}

variable "registry_name" {
  type        = string
  default     = "schema-registry"
  description = "Name of the Glue Schema Registry"
}

variable "registry_description" {
  type        = string
  default     = "Schema Registry for data contracts"
  description = "Description of the Glue Schema Registry"
}

variable "common_tags" {
  type = map(string)
  default = {
    Environment = "dev"
    Project     = "schema-registry"
    ManagedBy   = "terraform"
  }
  description = "Common tags to apply to all resources"
}