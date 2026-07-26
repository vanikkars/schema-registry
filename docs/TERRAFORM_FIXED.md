# Terraform AWS Credentials - FIXED ✅

## Problem Solved

**Issue:** Terraform couldn't find AWS credentials even though .env was set up

**Root Cause:** 
1. `AWS_PROFILE=default` in .env forced AWS SDK to look for a profile file (which didn't exist)
2. Terraform needed explicit `-var` flags with credentials passed after the subcommand

## Solution Implemented

### 1. ✅ Fixed .env File

Commented out `AWS_PROFILE=default`:
```bash
# AWS_PROFILE=default  # Commented out - using direct credentials instead
```

### 2. ✅ Updated Terraform Provider Configuration

Modified `infra/aws/main.tf` to:
- Accept `access_key` and `secret_key` variables
- Skip credentials validation
- Skip metadata API check
- Skip AWS config file reading

```hcl
provider "aws" {
  region                          = var.aws_region
  access_key                      = var.aws_access_key
  secret_key                      = var.aws_secret_key
  skip_credentials_validation     = true
  skip_metadata_api_check         = true
  skip_requesting_account_id      = true
  allowed_account_ids             = []
}
```

### 3. ✅ Created run_terraform.sh Script

Helper script that:
- Loads credentials from `../../.env`
- Exports AWS environment variables
- Disables AWS config file reading
- Passes credentials as `-var` flags to terraform

**Usage:**
```bash
bash run_terraform.sh plan
bash run_terraform.sh apply
bash run_terraform.sh destroy
```

### 4. ✅ Made Credential Variables Required

Updated `variables.tf` to make credentials required (no default empty strings):
```hcl
variable "aws_access_key" {
  type      = string
  sensitive = true
  # No default - required!
}
```

## How to Use

### Step 1: Setup Credentials

Edit your `.env` file:
```bash
nano .env
```

Make sure you have:
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
TF_VAR_aws_access_key=your_key
TF_VAR_aws_secret_key=your_secret
# AWS_PROFILE=default  ← MUST BE COMMENTED OUT
```

### Step 2: Run Terraform

From `infra/aws/` directory:

```bash
# Plan
bash run_terraform.sh plan

# Apply
bash run_terraform.sh apply

# Destroy
bash run_terraform.sh destroy

# Init (if needed)
bash run_terraform.sh init
```

### Step 3: Verify

Check outputs:
```bash
bash run_terraform.sh output
```

## What Terraform Will Create

✅ **AWS Glue Registry** - Central schema repository
- Name: `schema-registry`
- Description: `Schema Registry for data contracts`

✅ **User Schema** - AVRO format schema
- Name: `user-schema`
- Format: AVRO
- Compatibility: BACKWARD
- Fields: user_name, email, date_of_birth

## Complete Example

```bash
# From schema-registry/ root directory
cd infra/aws

# Check credentials are in .env
cat ../../.env | grep TF_VAR_aws

# Plan
bash run_terraform.sh plan

# Apply (creates resources)
bash run_terraform.sh apply

# View outputs
bash run_terraform.sh output

# Destroy (when done)
bash run_terraform.sh destroy
```

## Troubleshooting

### "No valid credential sources found"

**Solution:**
1. Uncomment `AWS_PROFILE=default` in .env → Comment it back out
2. Verify credentials are set: `cat .env | grep TF_VAR_aws`
3. Re-run: `bash run_terraform.sh plan`

### "AccessDenied"

Your IAM user needs these permissions:
- `glue:CreateRegistry`
- `glue:CreateSchema`
- `glue:PutSchemaVersion`
- `glue:GetRegistry`
- `glue:GetSchema`

### Terraform not finding .env

Make sure you're in the `infra/aws/` directory:
```bash
cd infra/aws
bash run_terraform.sh plan
```

## Files Modified

1. ✅ `.env` - Commented out AWS_PROFILE
2. ✅ `.env.example` - Updated template
3. ✅ `infra/aws/main.tf` - Updated provider configuration
4. ✅ `infra/aws/variables.tf` - Made credentials required
5. ✅ `infra/aws/terraform.auto.tfvars` - Updated
6. ✅ `infra/aws/run_terraform.sh` - Created helper script

## Next Steps

1. Verify .env has correct credentials and `AWS_PROFILE` is commented out
2. Run: `bash run_terraform.sh plan`
3. Review the plan
4. Run: `bash run_terraform.sh apply` to deploy
5. Run: `bash run_terraform.sh output` to see registry details

🚀 You're all set!