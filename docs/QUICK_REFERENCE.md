a# Quick Reference - Common Commands

## Setup (First Time)

```bash
# Copy environment template
cp .env.example .env

# Edit with your AWS credentials
nano .env

# Load environment variables
source .env

# Or use AWS CLI
aws configure
```

## Generate Contracts

```bash
# Generate contracts from Pydantic models
python contracts_management/generate_contract.py

# Output saved to: contracts/user_contract.json
```

## Deploy Infrastructure

```bash
# Navigate to infrastructure
cd infra/aws

# Initialize Terraform (first time only)
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply

# View outputs
terraform output

# Destroy (cleanup)
terraform destroy
```

## Upload Contracts to AWS Glue

```bash
# Using AWS CLI
aws glue put-schema-version \
  --registry-id RegistryName=schema-registry \
  --schema-name user-schema \
  --data-format AVRO \
  --compatibility BACKWARD \
  --schema-definition file://contracts/user_contract.json
```

## Verify Setup

```bash
# Check AWS credentials
aws sts get-caller-identity

# List registries
aws glue list-registries

# List schemas in registry
aws glue list-schemas \
  --registry-id RegistryName=schema-registry

# Get schema details
aws glue get-schema \
  --schema-id RegistryName=schema-registry,SchemaName=user-schema
```

## Terraform Troubleshooting

```bash
# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Show current state
terraform show

# Refresh state
terraform refresh

# Enable debug logging
export TF_LOG=DEBUG
terraform plan

# Unset debug logging
unset TF_LOG
```

## Environment Variables (for Terraform)

```bash
# AWS Credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1

# Terraform Variables
export TF_VAR_aws_region=us-east-1
export TF_VAR_registry_name=schema-registry
export TF_VAR_registry_description="Schema Registry for data contracts"
```

## File Paths

```
Project Root
├── .env                          # Your credentials (don't commit)
├── .env.example                  # Template (commit this)
├── app/models.py                 # Application models
├── contracts_management/
│   ├── generate_contract.py      # Run this to generate contracts
│   └── models.py                 # Contract models
├── contracts/                    # Generated contract files
│   └── user_contract.json        # Contract to upload
└── infra/aws/                    # Terraform code
    ├── main.tf                   # AWS resources
    ├── variables.tf              # Variable definitions
    └── terraform.tfvars          # Variable values
```

## Complete Workflow

```bash
# 1. Setup (first time)
cp .env.example .env
# Edit .env with your credentials

# 2. Load environment
source .env

# 3. Generate contracts
python contracts_management/generate_contract.py

# 4. Deploy infrastructure
cd infra/aws
terraform init
terraform plan
terraform apply
cd ../..

# 5. Upload contracts
aws glue put-schema-version \
  --registry-id RegistryName=schema-registry \
  --schema-name user-schema \
  --data-format AVRO \
  --compatibility BACKWARD \
  --schema-definition file://contracts/user_contract.json

# 6. Verify
aws glue get-schema \
  --schema-id RegistryName=schema-registry,SchemaName=user-schema
```

## Environment Variable Shortcuts

Create these aliases in your `.zshrc` or `.bashrc`:

```bash
# Load environment
alias sls='source .env'

# Navigate to infra
alias infra='cd infra/aws'

# Generate contracts
alias gencontracts='python contracts_management/generate_contract.py'

# Common Terraform commands
alias tfinit='terraform init'
alias tfplan='terraform plan'
alias tfapply='terraform apply'
alias tfdestroy='terraform destroy'
alias tfoutput='terraform output'
```

Then use:
```bash
sls              # source .env
gencontracts     # generate contracts
infra            # cd to infra/aws
tfapply          # terraform apply
```

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "Unable to locate credentials" | No AWS credentials | Run `aws configure` or set env vars |
| "InvalidClientTokenId" | Invalid AWS key/secret | Check `.env` or `aws configure` |
| "AccessDenied" | IAM permissions missing | Add Glue permissions to IAM user |
| "registry already exists" | Registry name taken | Change `TF_VAR_registry_name` |
| "terraform init required" | First time setup | Run `terraform init` |
| "No changes" after apply | Already deployed | Run `terraform plan` to check state |

## Pro Tips

1. **Before destroying:** Always run `terraform plan` first
2. **Safe apply:** Use `-auto-approve=false` (default) to review before applying
3. **Backup state:** `cp terraform.tfstate terraform.tfstate.backup`
4. **Check outputs:** Always run `terraform output` after apply
5. **Validate first:** Run `terraform validate` before apply

## Useful AWS CLI Commands

```bash
# Get AWS account ID
aws sts get-caller-identity --query Account

# List all Glue registries
aws glue list-registries

# Get registry details
aws glue get-registry --registry-id RegistryName=schema-registry

# List schemas in registry
aws glue list-schemas --registry-id RegistryName=schema-registry

# Get schema versions
aws glue list-schema-versions \
  --schema-id RegistryName=schema-registry,SchemaName=user-schema

# Get specific schema version
aws glue get-schema-version \
  --schema-version-id '{VersionNumber: 1, RegistryName: schema-registry, SchemaName: user-schema}'

# Delete schema version
aws glue delete-schema-versions \
  --schema-id RegistryName=schema-registry,SchemaName=user-schema \
  --versions 2,3
```

## Documentation

- `README.md` - Main project documentation
- `TERRAFORM_SETUP.md` - Detailed Terraform setup guide
- `PROJECT_STRUCTURE.md` - Folder organization
- `infra/README.md` - Infrastructure documentation
- `infra/aws/README.md` - AWS Glue documentation

See the appropriate doc for more details!