# Terraform Setup Guide

Quick reference for running Terraform with AWS credentials.

## Quick Start (5 minutes)

### 1. Setup AWS Credentials

```bash
# Option A: Using AWS CLI (recommended)
aws configure
# Enter your Access Key ID and Secret Access Key when prompted

# Option B: Using environment variables
export AWS_ACCESS_KEY_ID=your_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

### 2. Create .env file

```bash
cp .env.example .env
# Edit .env with your AWS credentials and Terraform variables
```

### 3. Deploy Infrastructure

```bash
# Load environment variables
source .env

# Navigate to infrastructure directory
cd infra/aws

# Initialize Terraform
terraform init

# Deploy
terraform plan
terraform apply
```

## Three Ways to Provide Credentials to Terraform

### Method 1: AWS CLI (Recommended)

```bash
# Configure once
aws configure

# Then just run Terraform
cd infra/aws
terraform init
terraform apply
```

**Advantages:**
- Secure credential storage
- Works across projects
- No credentials in git

**How it works:**
- Credentials stored in `~/.aws/credentials`
- Config in `~/.aws/config`
- Terraform uses AWS SDK which reads these files

### Method 2: Environment Variables

```bash
# Set credentials
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_REGION=us-east-1

# Run Terraform
cd infra/aws
terraform init
terraform apply
```

**Advantages:**
- Useful for CI/CD pipelines
- Programmatic access
- Easy to switch accounts

**Disadvantages:**
- Credentials visible in environment
- More secure to use IAM roles in production

### Method 3: .env File + Source

```bash
# Create .env with credentials
cat > .env << EOF
export AWS_ACCESS_KEY_ID=your_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
export TF_VAR_registry_name=schema-registry
EOF

# Source before running Terraform
source .env

cd infra/aws
terraform init
terraform apply
```

**Advantages:**
- Organized in one file
- Easy to share template (.env.example)
- Can store multiple variable settings

**Note:** Add `.env` to `.gitignore` to prevent credential leaks

## Terraform Variables

### Load Variables from Environment

```bash
# Set as environment variables
export TF_VAR_aws_region=us-east-1
export TF_VAR_registry_name=schema-registry
export TF_VAR_registry_description="Schema Registry for data contracts"

# Or in .env file
cat >> .env << EOF
TF_VAR_aws_region=us-east-1
TF_VAR_registry_name=schema-registry
TF_VAR_registry_description=Schema Registry for data contracts
EOF

source .env
```

### Load Variables from File

#### Option 1: terraform.tfvars (auto-loaded)

```hcl
# infra/aws/terraform.tfvars
aws_region      = "us-east-1"
registry_name   = "schema-registry"
registry_description = "Schema Registry for data contracts"

common_tags = {
  Environment = "dev"
  Project     = "schema-registry"
  ManagedBy   = "terraform"
}
```

Then just run:
```bash
terraform apply
```

#### Option 2: terraform.auto.tfvars (auto-loaded)

```bash
cat > infra/aws/terraform.auto.tfvars << EOF
aws_region      = "us-east-1"
registry_name   = "schema-registry"
registry_description = "Schema Registry for data contracts"

common_tags = {
  Environment = "dev"
  Project     = "schema-registry"
  ManagedBy   = "terraform"
}
EOF
```

#### Option 3: Custom .tfvars file

```bash
terraform apply -var-file="custom.tfvars"
```

### Command-line Variables

```bash
terraform apply \
  -var="aws_region=us-east-1" \
  -var="registry_name=schema-registry" \
  -var="registry_description=Schema Registry for data contracts"
```

## Complete Example

### Step 1: Setup

```bash
# From project root
cp .env.example .env

# Edit .env
nano .env
```

### Step 2: Configure AWS

```bash
# Option A: AWS CLI
aws configure
# When prompted:
# AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name: us-east-1
# Default output format: json

# Option B: Use .env
source .env
```

### Step 3: Deploy

```bash
cd infra/aws

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply

# View outputs
terraform output
```

### Step 4: Verify

```bash
# List resources
aws glue list-registries --region us-east-1

# Get registry details
aws glue get-registry \
  --registry-id RegistryName=schema-registry \
  --region us-east-1
```

### Step 5: Upload Contracts

```bash
# From project root
aws glue put-schema-version \
  --registry-id RegistryName=schema-registry \
  --schema-name user-schema \
  --data-format AVRO \
  --compatibility BACKWARD \
  --schema-definition file://contracts/user_contract.json \
  --region us-east-1
```

## Troubleshooting

### "InvalidClientTokenId" Error

**Cause:** Invalid AWS credentials

**Solution:**
```bash
# Check credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

### "AccessDenied" Error

**Cause:** IAM permissions insufficient

**Solution:**
Ensure IAM user/role has these permissions:
- `glue:CreateRegistry`
- `glue:CreateSchema`
- `glue:PutSchemaVersion`
- `glue:GetRegistry`
- `glue:GetSchema`

### "Unable to locate credentials" Error

**Cause:** No credentials configured

**Solution:**
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

### Terraform State Issues

```bash
# View current state
terraform show

# Backup state before making changes
cp terraform.tfstate terraform.tfstate.backup

# Refresh state from AWS
terraform refresh
```

## Security Best Practices

1. **Never commit credentials**
   - Add `.env` to `.gitignore`
   - Use `.env.example` for template

2. **Use AWS CLI securely**
   - Store credentials in `~/.aws/credentials`
   - Protect file permissions: `chmod 600 ~/.aws/credentials`

3. **Use IAM roles in production**
   - Avoid long-term access keys
   - Use STS temporary credentials
   - Rotate keys regularly

4. **Audit access**
   - Enable CloudTrail
   - Monitor API calls
   - Review S3 bucket access logs

## Additional Resources

- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [Terraform Variable Documentation](https://www.terraform.io/docs/language/values/variables.html)
- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)