# Infrastructure as Code

This directory contains Terraform configurations for provisioning cloud infrastructure.

## Structure

```
infra/
├── aws/
│   ├── main.tf              # Main Terraform configuration
│   ├── variables.tf         # Variable definitions
│   ├── terraform.tfvars     # Variable values for development
│   ├── backend.tf           # Remote state configuration (optional)
│   └── README.md            # AWS-specific documentation
└── README.md                # This file
```

## AWS Glue Schema Registry

The Terraform configuration provisions an AWS Glue Schema Registry to store and manage data contracts.

### What gets created:

1. **Schema Registry** - Central repository for all data schemas
2. **User Schema** - AVRO schema for user data contract

### Prerequisites

- AWS Account with appropriate IAM permissions
- Terraform >= 1.0
- AWS CLI configured with credentials

### Setup

1. Load environment variables from project root:
   ```bash
   cd ../..
   source .env
   cd infra/aws
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Create terraform.auto.tfvars (optional, auto-loads variables):
   ```bash
   cat > terraform.auto.tfvars << EOF
   aws_region = "$AWS_REGION"
   registry_name = "$TF_VAR_registry_name"
   registry_description = "$TF_VAR_registry_description"
   common_tags = {
     Environment = "dev"
     Project     = "schema-registry"
     ManagedBy   = "terraform"
   }
   EOF
   ```

4. Plan the deployment:
   ```bash
   terraform plan
   ```

5. Apply the configuration:
   ```bash
   terraform apply
   ```

### Configuration

### Method 1: Using .env file (Recommended)

Create `.env` in project root (copy from `.env.example`):

```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
TF_VAR_registry_name=schema-registry
TF_VAR_registry_description=Schema Registry for data contracts
```

Load before running Terraform:

```bash
source ../../.env
terraform plan
terraform apply
```

### Method 2: Using terraform.tfvars

Edit `terraform.tfvars` to customize:
- AWS region
- Registry name
- Tags and environment settings

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

### Method 3: Using terraform.auto.tfvars

Auto-loads variables without needing to specify `-var-file`:

```bash
cat > terraform.auto.tfvars << EOF
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

### Method 4: Command-line Variables

Pass variables directly to Terraform commands:

```bash
terraform plan \
  -var="aws_region=us-east-1" \
  -var="registry_name=schema-registry"

terraform apply \
  -var="aws_region=us-east-1" \
  -var="registry_name=schema-registry"
```

### Remote State

To use S3 backend for state management:

1. Create S3 bucket and DynamoDB table for state locking
2. Uncomment and update the `backend` block in `backend.tf`
3. Run `terraform init` to migrate state

### Outputs

After applying, Terraform outputs:
- Schema Registry ARN
- Schema ARN
- Schema Version ID

Use these to interact with the registry programmatically.

### Cleanup

To destroy all resources:
```bash
terraform destroy
```