# AWS Glue Schema Registry

Terraform configuration for AWS Glue Schema Registry.

## Setup

### Prerequisites

Configure AWS credentials (choose one):

**Option A: AWS CLI**
```bash
aws configure
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

**Option C: .env File**
```bash
source ../../.env
```

### Deploy

```bash
# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply
```

## Configuration

### Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | us-east-1 | AWS region |
| `registry_name` | schema-registry | Registry name |
| `registry_description` | Schema Registry for data contracts | Description |
| `common_tags` | See tfvars | Resource tags |

### Set Variables

**Option 1: terraform.tfvars** (auto-loaded)
```hcl
aws_region      = "us-east-1"
registry_name   = "schema-registry"
registry_description = "Schema Registry for data contracts"
```

**Option 2: terraform.auto.tfvars** (overrides tfvars)
```bash
cat > terraform.auto.tfvars << 'EOF'
aws_region = "us-east-1"
registry_name = "schema-registry"
registry_description = "Schema Registry for data contracts"
common_tags = {
  Environment = "dev"
  Project     = "schema-registry"
  ManagedBy   = "terraform"
}
EOF
```

**Option 3: Environment Variables**
```bash
source ../../.env
terraform apply
```

**Option 4: Command-line**
```bash
terraform plan \
  -var="aws_region=us-east-1" \
  -var="registry_name=schema-registry"
```

## Files

| File | Purpose |
|------|---------|
| `main.tf` | Schema Registry resource |
| `variables.tf` | Input variable definitions |
| `outputs.tf` | Output values |
| `terraform.tfvars` | Default variable values |
| `backend.tf` | Remote state config (optional) |

## Workflow

```bash
# From project root
source .env
cd infra/aws

# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply -auto-approve

# View outputs
terraform output
```

## Outputs

```bash
terraform output schema_registry_arn
terraform output schema_registry_name
```

## Cleanup

```bash
terraform destroy
```

Confirm by typing `yes`.

## Remote State (S3 Backend)

Enable S3 backend for team collaboration:

1. Create S3 bucket and DynamoDB table
2. Uncomment backend block in `backend.tf`
3. Run `terraform init` to migrate

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "schema-registry/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

## Commands

```bash
# Validate syntax
terraform validate

# Format files
terraform fmt

# View current state
terraform show

# Refresh state from AWS
terraform refresh

# Targeted apply
terraform apply -target=aws_glue_schema_registry.main

# Debug
export TF_LOG=DEBUG
terraform plan
```

## Troubleshooting

### AWS credentials error
```bash
# Check AWS CLI
aws sts get-caller-identity

# Or source .env
source ../../.env
terraform init
```

### State lock
```bash
terraform force-unlock <LOCK_ID>
```

### Permission denied
Ensure IAM user/role has permissions:
- `glue:CreateRegistry`
- `glue:CreateSchema`
- `glue:GetRegistry`
- `glue:GetSchema`
- `glue:TagResource`

### Already exists
If registry already exists, import it:
```bash
terraform import aws_glue_schema_registry.main schema-registry
```

## See Also

- [Infrastructure Setup](../README.md)
- [API Documentation](../../registry_api/README.md)
- [Main README](../../README.md)
