# Infrastructure

Terraform configurations for AWS Glue Schema Registry.

## Quick Setup

```bash
# Navigate to AWS directory
cd infra/aws

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply changes
terraform apply
```

## Configuration

### Method 1: Environment Variables (Recommended)

From project root:
```bash
source .env
cd infra/aws
terraform plan
terraform apply
```

Requires these in `.env`:
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
TF_VAR_registry_name=schema-registry
TF_VAR_registry_description=Schema Registry for data contracts
```

### Method 2: terraform.tfvars

Edit `aws/terraform.tfvars`:
```hcl
aws_region      = "us-east-1"
registry_name   = "schema-registry"
registry_description = "Schema Registry for data contracts"

common_tags = {
  Environment = "dev"
  Project     = "schema-registry"
  ManagedBy   = "terraform"
}
```

### Method 3: Command-line Variables

```bash
terraform plan \
  -var="aws_region=us-east-1" \
  -var="registry_name=schema-registry"
```

## Structure

```
infra/
├── aws/
│   ├── main.tf              # Registry + schema definitions
│   ├── variables.tf         # Input variables
│   ├── outputs.tf          # Output values
│   ├── terraform.tfvars    # Variable values
│   └── README.md
└── README.md
```

## Resources Created

- **AWS Glue Schema Registry** - Central schema repository
- **AVRO Schema Support** - For schema versioning
- **Compatibility Mode** - BACKWARD compatibility enabled

## Commands

```bash
cd infra/aws

# Initialize
terraform init

# Validate configuration
terraform validate

# View plan
terraform plan

# Apply changes
terraform apply

# View outputs
terraform output

# Destroy resources
terraform destroy
```

## Outputs

After applying, get values with:
```bash
terraform output schema_registry_arn
terraform output schema_registry_name
```

Or view all:
```bash
terraform output
```

## State Management

Default: Local state in `terraform.tfstate`

For remote state (S3 backend):
1. Create S3 bucket and DynamoDB table
2. Uncomment backend block in `backend.tf`
3. Run `terraform init` to migrate

## Troubleshooting

### AWS credentials not found
```bash
source ../../.env
terraform plan
```

### State lock
```bash
terraform force-unlock <LOCK_ID>
```

### Format issues
```bash
terraform fmt -recursive
```

## See Also

- [AWS Setup Details](aws/README.md)
- [Main README](../README.md)
