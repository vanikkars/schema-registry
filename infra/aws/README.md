# AWS Glue Schema Registry

Terraform configuration for AWS Glue Schema Registry with data contracts.

## Files

- `main.tf` - Creates Glue Schema Registry and schemas
- `variables.tf` - Input variables
- `terraform.tfvars` - Variable values
- `backend.tf` - Remote state configuration (optional)

## Resources Created

### AWS Glue Schema Registry
- Central registry to manage all data schemas
- Supports versioning and schema evolution
- Integrates with AWS Glue, Lambda, Kinesis, etc.

### User Schema
- AVRO format schema for user data
- Backward compatible schema evolution
- Includes fields: user_name, email, date_of_birth

## Usage

### Prerequisites

Ensure AWS credentials are configured. Choose one method:

**Option A: AWS CLI (Recommended)**
```bash
aws configure
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

**Option C: .env file**
```bash
source ../../.env
```

### 1. Initialize

```bash
cd infra/aws
terraform init
```

### 2. Create Variables File (Optional)

Auto-load variables without passing flags:

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

Or use existing `terraform.tfvars`:

```bash
# Just run Terraform normally - variables load automatically
```

### 3. Plan

```bash
terraform plan
```

Or with specific variables:

```bash
terraform plan \
  -var="aws_region=us-east-1" \
  -var="registry_name=my-registry"
```

### 4. Deploy

```bash
terraform apply
```

Or with specific variables:

```bash
terraform apply \
  -var="aws_region=us-east-1" \
  -var="registry_name=my-registry"
```

### 5. View Outputs

```bash
terraform output
```

Get specific output:

```bash
terraform output schema_registry_arn
```

## Terraform Workflow

### Full Workflow with Environment Variables

```bash
# From project root
source .env

# Navigate to infra
cd infra/aws

# Initialize
terraform init

# Plan and apply
terraform plan
terraform apply -auto-approve

# View outputs
terraform output
```

### Destroy Resources

```bash
cd infra/aws
terraform destroy
```

Confirm the destruction by typing `yes`.

## Uploading Contracts

After creating the registry and getting outputs, you can register schemas:

```bash
aws glue put-schema-version \
  --registry-id RegistryName=schema-registry \
  --schema-name user-schema \
  --data-format AVRO \
  --compatibility BACKWARD \
  --schema-definition file://contracts/user_contract.json
```

Or use the Python SDK:

```python
import boto3
import json

glue = boto3.client('glue', region_name='us-east-1')

with open('contracts/user_contract.json', 'r') as f:
    schema_def = f.read()

response = glue.put_schema_version(
    RegistryId={'RegistryName': 'schema-registry'},
    SchemaName='user-schema',
    DataFormat='AVRO',
    Compatibility='BACKWARD',
    SchemaDefinition=schema_def
)

print(f"Schema Version: {response['VersionNumber']}")
```

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | us-east-1 | AWS region for resources |
| `registry_name` | schema-registry | Name of the registry |
| `registry_description` | Schema Registry for data contracts | Registry description |
| `common_tags` | See tfvars | Tags for all resources |

## Outputs

```bash
terraform output
```

Returns:
- `schema_registry_arn` - ARN of the registry
- `schema_registry_name` - Name of the registry
- `user_schema_arn` - ARN of user schema
- `user_schema_version` - Version ID of schema