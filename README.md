# Schema Registry

A FastAPI-based data contract management system with AWS Glue Schema Registry integration.

## Overview

This project provides a complete solution for:
- Defining application data models with Pydantic
- Generating formal data contracts from those models
- Storing contracts in JSON format
- Provisioning AWS Glue Schema Registry via Terraform
- Managing schema versioning and evolution

## Project Structure

```
schema-registry/
├── app/                             # Application domain models
│   ├── __init__.py
│   └── models.py                   # User and other app models
├── contracts_management/            # Contract generation and management
│   ├── __init__.py
│   ├── models.py                   # DataContract, ContractMetadata, ColumnDefinition
│   ├── generate_contract.py        # Generate contracts from Pydantic models
│   └── upload_to_glue.py           # CLI for uploading to registry
├── contracts/                       # Generated data contracts (JSON)
│   ├── user_contract.json
│   ├── test_contract.json
│   └── transaction_contract.json
├── infra/                           # Infrastructure as Code
│   ├── aws/                         # AWS Glue Schema Registry (Terraform)
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   ├── backend.tf
│   │   └── README.md
│   └── README.md
├── registry-api/                    # FastAPI service for schema registry
│   ├── __init__.py
│   ├── main.py                     # FastAPI application
│   ├── api.py                      # API endpoints and client
│   ├── run.sh                      # Startup script
│   └── README.md                   # Service documentation
├── PROJECT_STRUCTURE.md            # Detailed structure documentation
└── API_USAGE.md                    # API documentation
```

## Setup & Configuration

### Prerequisites

- Python 3.10+
- Terraform >= 1.0
- AWS Account with appropriate IAM permissions
- AWS CLI configured

### Environment Setup

1. Clone the repository and navigate to the project directory

2. Create a `.env` file from the example:

```bash
cp .env.example .env
```

3. Update `.env` with your AWS credentials:

```bash
# .env
AWS_ACCESS_KEY_ID=your_actual_access_key
AWS_SECRET_ACCESS_KEY=your_actual_secret_key
AWS_REGION=us-east-1
AWS_PROFILE=default

# Optional: Terraform variables
TF_VAR_aws_region=us-east-1
TF_VAR_registry_name=schema-registry
TF_VAR_registry_description=Schema Registry for data contracts
```

4. Load environment variables:

```bash
# macOS/Linux
source .env

# Windows (PowerShell)
Get-Content .env | ForEach-Object {
    if ($_ -and !$_.StartsWith('#')) {
        [Environment]::SetEnvironmentVariable($_.Split('=')[0], $_.Split('=')[1], 'Process')
    }
}
```

## Quick Start

### 1. Define Application Models

Create Pydantic models in `app/models.py`:

```python
from pydantic import BaseModel, Field
from datetime import date

class User(BaseModel):
    user_name: str = Field(..., description="Username for the user")
    email: str = Field(..., description="Email address of the user")
    date_of_birth: date = Field(..., description="Date of birth in YYYY-MM-DD format")
```

### 2. Generate Data Contracts

Run the contract generation script:

```bash
python contracts_management/generate_contract.py
```

This creates `contracts/user_contract.json` with:
- Column definitions
- Data types and nullability
- Metadata (owner, steward, SLAs)
- Timestamps

### 3. Deploy AWS Glue Schema Registry

#### Option 1: Using Environment Variables (Recommended)

```bash
# Load environment variables
source .env

# Navigate to AWS infrastructure
cd infra/aws

# Initialize Terraform
terraform init

# Create terraform.auto.tfvars from environment variables
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

# Plan and apply
terraform plan
terraform apply
```

#### Option 2: Using terraform.tfvars

Edit `infra/aws/terraform.tfvars`:

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

Then run:

```bash
cd infra/aws
terraform init
terraform plan
terraform apply
```

#### Option 3: Using Command-line Variables

```bash
cd infra/aws
terraform init

terraform plan \
  -var="aws_region=us-east-1" \
  -var="registry_name=schema-registry" \
  -var="registry_description=Schema Registry for data contracts"

terraform apply \
  -var="aws_region=us-east-1" \
  -var="registry_name=schema-registry" \
  -var="registry_description=Schema Registry for data contracts"
```

### 4. Upload Contracts to Registry

Using AWS CLI:

```bash
aws glue put-schema-version \
  --registry-id RegistryName=schema-registry \
  --schema-name user-schema \
  --data-format AVRO \
  --compatibility BACKWARD \
  --schema-definition file://contracts/user_contract.json
```

Or using Python:

```python
import boto3
import json

glue = boto3.client('glue', region_name='us-east-1')

with open('contracts/user/user_contract.json', 'r') as f:
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


## Create a contract via schema registry
```bash
curl -X POST "http://localhost:8000/api/v1/schemas/register" \
    -H "Content-Type: application/json" \
    -d @contracts/user_contract.json
```

response
```bash
{
    "status":"success",
    "message":"Schema registered successfully",
    "schema_arn":"arn:aws:glue:us-east-1:700308877625:schema/schema-registry/users-v1",
    "schema_name":"users-v1",
    "version":"1.0.0"
}
```
### in UI
high level
![img.png](images/high-level.png)

schema
![img.png](images/the-schema.png)

metadata
![img.png](images/the-metadata.png)

```bash
curl  -i http://localhost:8000/api/v1/schemas/detail/users-v1
curl  -i http://localhost:8000/api/v1/schemas/versions/users-v1
```


## Key Components

### Application Models (`app/models.py`)

Define your domain models using Pydantic:
- Type validation
- JSON schema generation
- Field descriptions and constraints

### Contract Models (`contracts_management/models.py`)

Formal Pydantic models for data contracts:
- `DataContract` - Main contract definition
- `ContractMetadata` - Owner, steward, SLAs
- `ColumnDefinition` - Individual column specs

### Contract Generation (`contracts_management/generate_contract.py`)

Automatically converts Pydantic models to data contracts:
- Extracts schema information
- Maps Python types to contract types
- Generates JSON artifacts
- Supports metadata and versioning

### Infrastructure (`infra/aws/`)

Terraform configuration for AWS Glue:
- Creates Schema Registry
- Defines schemas with versioning
- Supports backward/forward compatibility
- Integrates with AWS services

## Data Contract Example

Generated `contracts/user_contract.json`:

```json
{
  "contract_id": "users-v1",
  "name": "Users",
  "description": "Schema for user records",
  "version": "1.0.0",
  "columns": [
    {
      "name": "user_name",
      "data_type": "string",
      "nullable": false,
      "description": "Username for the user"
    },
    {
      "name": "email",
      "data_type": "string",
      "nullable": false,
      "description": "Email address of the user"
    },
    {
      "name": "date_of_birth",
      "data_type": "date",
      "nullable": false,
      "description": "Date of birth in YYYY-MM-DD format"
    }
  ],
  "metadata": {
    "data_owner": "User Management",
    "data_owner_email": "user-mgmt@company.com",
    "data_steward": "Data Engineering",
    "data_steward_email": "data-engineering@company.com",
    "sla_uptime_percentage": 99.95,
    "sla_max_latency_ms": 5000
  },
  "created_at": "2026-07-26T09:55:56.015794+00:00",
  "updated_at": "2026-07-26T09:55:56.015794+00:00"
}
```

## Workflow

```
1. Define Models
   └─→ app/models.py

2. Generate Contracts
   └─→ contracts_management/generate_contract.py
   └─→ contracts/*.json

3. Version Control
   └─→ Commit contracts to git

4. Deploy Infrastructure
   └─→ infra/aws/ (Terraform)
   └─→ AWS Glue Schema Registry

5. Upload Contracts
   └─→ aws glue put-schema-version
   └─→ Schema Registry
```

## AWS Credentials

### Using AWS CLI

Configure your AWS credentials:

```bash
aws configure
```

This creates `~/.aws/credentials` and `~/.aws/config`

### Using Environment Variables

Set AWS credentials as environment variables in `.env`:

```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
```

### Using AWS Profile

If you have multiple AWS profiles configured:

```bash
export AWS_PROFILE=my-profile
cd infra/aws
terraform init
terraform apply
```

### Using IAM Role (Recommended for CI/CD)

If running on AWS resources (EC2, Lambda, etc.), use IAM roles:

```bash
# No credentials needed - IAM role will be used automatically
terraform init
terraform apply
```

## Requirements

- Python 3.10+
- Pydantic 2.0+
- AWS Account with IAM permissions for Glue
- Terraform >= 1.0
- AWS CLI configured or credentials in `.env`

## Development

### Generate contracts locally:

```bash
python contracts_management/generate_contract.py
```

### Terraform Commands

#### Validate configuration:

```bash
cd infra/aws
terraform validate
terraform fmt
```

#### View current state:

```bash
cd infra/aws
terraform show
```

#### View outputs:

```bash
cd infra/aws
terraform output
```

#### Destroy resources (cleanup):

```bash
cd infra/aws
source ../../.env  # Load AWS credentials
terraform destroy
```

#### Troubleshooting Terraform:

```bash
# Enable debug logging
export TF_LOG=DEBUG
terraform plan

# Format Terraform files
terraform fmt -recursive

# Validate all configurations
terraform validate

# Check for security issues
terraform plan -json | tfsec --json
```

### Complete Development Workflow:

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your AWS credentials

# 2. Load environment variables
source .env

# 3. Generate contracts
python contracts_management/generate_contract.py

# 4. Deploy infrastructure
cd infra/aws
terraform init
terraform plan
terraform apply

# 5. View outputs
terraform output

# 6. Upload contracts to registry
cd ../..
aws glue put-schema-version \
  --registry-id RegistryName=schema-registry \
  --schema-name user-schema \
  --data-format AVRO \
  --compatibility BACKWARD \
  --schema-definition file://contracts/user_contract.json
```

## API Integration (Future)

This project can be integrated with FastAPI for:
- Schema registry endpoints
- Contract versioning APIs
- Contract validation
- Schema evolution tracking

## Contributing

1. Add new models to `app/models.py`
2. Generate contracts
3. Update infrastructure if needed
4. Commit changes

## License

MIT

## Documentation

- [Project Structure](docs/PROJECT_STRUCTURE.md) - Detailed folder organization
- [AWS Infrastructure](infra/aws/README.md) - Terraform configuration details
- [Contract Management](infra/README.md) - Infrastructure setup guide
