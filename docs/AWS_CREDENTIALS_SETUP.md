# AWS Credentials Setup Guide

## Problem

Terraform needs AWS credentials to authenticate with AWS. The error "No valid credential sources found" means Terraform can't find your credentials.

## Solution

### Step 1: Get Your AWS Credentials

1. Log in to your AWS Sandbox Console:
   ```
   https://079059455177.signin.aws.amazon.com/console?region=us-east-1
   ```

2. Navigate to **IAM** → **Users** → **Your Username**

3. Go to the **Security Credentials** tab

4. Under **Access Keys**, click **Create access key**

5. Save your:
   - Access Key ID
   - Secret Access Key

### Step 2: Update .env File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and replace with your credentials:
   ```bash
   nano .env
   ```

3. Update these lines with your actual credentials:
   ```bash
   AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
   AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   TF_VAR_aws_access_key=AKIAIOSFODNN7EXAMPLE
   TF_VAR_aws_secret_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```

### Step 3: Source Environment Variables

Before running Terraform, load your credentials:

```bash
source .env
```

Verify they're loaded:
```bash
echo $AWS_ACCESS_KEY_ID
echo $TF_VAR_aws_access_key
```

### Step 4: Run Terraform

```bash
cd infra/aws
terraform plan
terraform apply
```

## Important Notes

### Credential Variables Required

Terraform needs **TWO** sets of variables:

1. **AWS CLI variables** (optional, for manual AWS CLI usage):
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`

2. **Terraform variables** (REQUIRED for Terraform):
   - `TF_VAR_aws_access_key`
   - `TF_VAR_aws_secret_key`
   - `TF_VAR_aws_region`

Both use the same credentials, just with different names.

### Security Notes

⚠️ **IMPORTANT:**

- ✅ `.env` is in `.gitignore` - it won't be committed to git
- ✅ Never commit credentials to version control
- ✅ Keep your `.env` file private
- ✅ Rotate access keys regularly in AWS console
- ✅ Delete unused access keys

### Complete Workflow

```bash
# 1. Get credentials from AWS console
# (https://079059455177.signin.aws.amazon.com/console?region=us-east-1)

# 2. Copy and edit .env
cp .env.example .env
nano .env  # Add your credentials

# 3. Load environment
source .env

# 4. Verify credentials loaded
echo "Access Key: $TF_VAR_aws_access_key"

# 5. Generate contracts
python contracts_management/generate_contract.py

# 6. Deploy infrastructure
cd infra/aws
terraform init
terraform plan
terraform apply

# 7. View outputs
terraform output
```

## Troubleshooting

### Still Getting "No valid credential sources found"?

1. **Check if .env was sourced:**
   ```bash
   echo $TF_VAR_aws_access_key
   ```
   Should output your access key.

2. **Check if you're in the right directory:**
   ```bash
   pwd
   # Should be: /path/to/schema-registry/infra/aws
   ```

3. **Verify credentials are correct:**
   ```bash
   aws sts get-caller-identity
   # If this works, AWS CLI is configured correctly
   ```

4. **Try re-sourcing .env:**
   ```bash
   source ../../.env
   terraform plan
   ```

### "InvalidClientTokenId" Error?

Your credentials are invalid. Check:
- Access Key ID matches what's in AWS console
- Secret Access Key matches exactly (no typos)
- Keys are still active (not deleted)

### "AccessDenied" Error?

Your IAM user doesn't have permission to use Glue. Add these permissions:
- `glue:CreateRegistry`
- `glue:CreateSchema`
- `glue:GetRegistry`
- `glue:GetSchema`

## One-Liner Setup

After editing `.env`:

```bash
source .env && cd infra/aws && terraform plan
```

Or in one script:

```bash
#!/bin/bash
source .env
cd infra/aws
terraform init
terraform plan
terraform apply
terraform output
```
