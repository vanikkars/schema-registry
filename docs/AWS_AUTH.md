# AWS Authentication for Registry API

How the registry-api authorizes with AWS and where credentials come from.

## Credential Flow

### How boto3 Finds Credentials

When the registry-api starts, `boto3.client("glue")` looks for credentials in this order:

1. **Environment Variables** (highest priority)
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`

2. **IAM Role** (if running on AWS)
   - EC2 instance role
   - ECS task role
   - Lambda execution role

3. **AWS Credentials File** (lower priority)
   - `~/.aws/credentials`
   - `~/.aws/config`

4. **Container Credentials** (if using Docker)
   - ECS task metadata
   - EC2 instance metadata

## In Your Setup

### Local Development

When you run:
```bash
source .env
python registry_api/main.py
```

**Flow:**
1. `source .env` loads credentials into environment variables
2. FastAPI starts
3. `SchemaRegistryClient.__init__()` creates `boto3.client("glue")`
4. boto3 reads `AWS_ACCESS_KEY_ID` from environment
5. boto3 authenticates with AWS Glue

### Docker Container

When you run:
```bash
docker-compose up -d
```

**Flow:**
1. docker-compose reads `.env` file (via `env_file: .env`)
2. Credentials injected into container environment
3. Container starts FastAPI
4. `SchemaRegistryClient.__init__()` creates boto3 client
5. boto3 reads credentials from container environment

```yaml
# docker-compose.yml
services:
  registry-api:
    env_file:
      - .env  # Loads AWS credentials into container
    environment:
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION:-us-east-1}
```

## Code Implementation

The auth happens in `registry-api/api.py`:

```python
class SchemaRegistryClient:
    def __init__(self, region: str = "us-east-1"):
        # boto3 automatically looks for credentials in:
        # 1. Environment variables (from .env)
        # 2. IAM role (if on AWS)
        # 3. ~/.aws/credentials
        self.glue = boto3.client("glue", region_name=region)
```

**How it works:**
1. `boto3.client()` uses boto3's built-in credential finder
2. Searches in order (env vars first)
3. Returns authenticated client
4. All subsequent Glue API calls use this client's credentials

## Credential Sources by Environment

### Development (Local)

```bash
# Load from .env
source .env

# Start API
python registry_api/main.py

# Credentials used:
# - AWS_ACCESS_KEY_ID (from .env)
# - AWS_SECRET_ACCESS_KEY (from .env)
# - AWS_DEFAULT_REGION (from .env, defaults to us-east-1)
```

### Docker (Local)

```bash
# Start container
docker-compose up -d

# Credentials used:
# - env_file: .env (docker-compose reads this)
# - Environment variables passed to container
# - boto3 reads from container environment
```

### AWS Deployment (EC2, ECS, Lambda)

**No credentials needed in code!** Use IAM roles:

```bash
# On EC2 instance with IAM role, no .env needed
docker-compose up -d

# boto3 automatically:
# 1. Detects EC2 instance metadata
# 2. Assumes the IAM role
# 3. Gets temporary credentials
# 4. Uses those for AWS API calls
```

### Kubernetes Deployment

Use IRSA (IAM Roles for Service Accounts):

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/schema-registry-role

---
apiVersion: v1
kind: Pod
metadata:
  serviceAccountName: schema-registry-sa
spec:
  containers:
  - name: registry-api
    image: schema-registry:latest
    # No credentials needed - IRSA handles it
```

## Security Best Practices

### ❌ DO NOT

```bash
# ❌ Hardcode credentials in code
AWS_ACCESS_KEY_ID = "AKIA..."

# ❌ Commit .env to git
git add .env

# ❌ Log credentials
print(f"Using key: {AWS_ACCESS_KEY_ID}")

# ❌ Pass credentials in URLs
f"s3://bucket?key={AWS_ACCESS_KEY_ID}"
```

### ✅ DO

```bash
# ✅ Use environment variables
AWS_ACCESS_KEY_ID from .env

# ✅ Ignore .env in .gitignore
echo ".env" >> .gitignore

# ✅ Use IAM roles in production
# No credentials in code

# ✅ Rotate credentials regularly
# Generate new access keys monthly

# ✅ Use least privilege
# Only allow Glue permissions needed
```

## Verifying Credentials Work

### Test Locally

```bash
# Load credentials
source .env

# Test boto3 can authenticate
python -c "
import boto3
glue = boto3.client('glue', region_name='us-east-1')
try:
    response = glue.list_registries()
    print('✅ Authentication successful!')
    print(f'Found {len(response[\"Registries\"])} registries')
except Exception as e:
    print(f'❌ Authentication failed: {e}')
"
```

### Test in Docker

```bash
# Start container
docker-compose up -d

# Run test inside container
docker-compose exec registry-api python -c "
import boto3
glue = boto3.client('glue', region_name='us-east-1')
try:
    response = glue.list_registries()
    print('✅ Authentication successful in Docker!')
except Exception as e:
    print(f'❌ Authentication failed: {e}')
"

# Or just call the API
curl http://localhost:8000/api/v1/schemas/list
# If this works, credentials are valid
```

### Check Environment Variables

```bash
# Local
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Docker
docker-compose exec registry-api env | grep AWS_
```

## Troubleshooting Auth Issues

### Error: "Unable to locate credentials"

**Cause:** Credentials not found in any source

**Fix:**
```bash
# Local development
source .env
python registry_api/main.py

# Docker
docker-compose down
docker-compose up -d  # Ensure .env is loaded
```

### Error: "InvalidClientTokenId"

**Cause:** Credentials are wrong or expired

**Fix:**
```bash
# Check credentials
cat .env | grep AWS_

# Regenerate access keys in AWS console
# https://079059455177.signin.aws.amazon.com/console
# IAM → Users → Your User → Security Credentials
# Create new access key and update .env

# Verify new credentials
source .env
python -c "import boto3; boto3.client('glue').list_registries()"
```

### Error: "AccessDenied" or "Not Authorized to perform"

**Cause:** IAM user doesn't have required permissions

**Fix:**
```bash
# Add Glue permissions to IAM user
# AWS Console → IAM → Users → Your User → Permissions
# Add policy: AWSGlueFullAccess (or create custom policy)

# Required permissions:
# - glue:GetRegistry
# - glue:GetSchema
# - glue:CreateSchema
# - glue:PutSchemaVersion
# - glue:ListSchemas
# - glue:GetSchemaVersion
```

## Credential Rotation

### Local Development

```bash
# Every month, generate new access keys:
# 1. Go to AWS Console
#    https://079059455177.signin.aws.amazon.com/console
# 2. IAM → Users → Your User → Security Credentials
# 3. Create new access key
# 4. Update .env with new credentials
# 5. Delete old access key

# Verify new credentials work
source .env
curl http://localhost:8000/api/v1/schemas/list
```

### Docker Production

Use temporary credentials:

```bash
# Option 1: Use IAM role (automatic rotation)
# Deploy on EC2 with IAM role attached
# boto3 automatically gets new credentials every hour

# Option 2: Use AWS STS temporary credentials
export AWS_ACCESS_KEY_ID=...temporary...
export AWS_SECRET_ACCESS_KEY=...temporary...
export AWS_SESSION_TOKEN=...token...
docker-compose up -d

# Option 3: Use Secrets Manager
# Fetch credentials at startup
# Not covered in this guide
```

## Monitoring Access

### CloudTrail Logging

Enable CloudTrail to audit all API calls:

```bash
# AWS Console → CloudTrail → Create Trail
# Select S3 bucket for logs
# CloudWatch Logs group for monitoring

# View logs to see who called what
# aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=schema-registry
```

### CloudWatch Alarms

```bash
# Monitor failed authentication attempts
# CloudWatch → Metrics → CloudTrail
# Create alarm if UnauthorizedOperation count > threshold
```

## Production Recommendations

### For AWS Deployment

**Use IAM Roles** (no credentials in code):

```yaml
# EC2 Instance Profile
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetRegistry",
        "glue:GetSchema",
        "glue:CreateSchema",
        "glue:PutSchemaVersion",
        "glue:ListSchemas"
      ],
      "Resource": "*"
    }
  ]
}
```

### For On-Premise Deployment

**Use Access Keys**:

```bash
# Store in secure secret manager
# Not in .env files

# Options:
# 1. AWS Secrets Manager
# 2. HashiCorp Vault
# 3. Docker Secrets (for Swarm)
# 4. Kubernetes Secrets (for K8s)
```

### For CI/CD Pipelines

**Use GitHub Actions Secrets**:

```yaml
# .github/workflows/deploy.yml
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  AWS_REGION: us-east-1

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker-compose up -d
```

## Summary

| Environment | Credential Source | How It Works |
|-------------|-------------------|--------------|
| Local Dev | `.env` file | `source .env` loads vars, boto3 reads from env |
| Docker Local | `.env` (docker-compose) | docker-compose passes .env to container |
| EC2 | IAM Instance Role | boto3 queries metadata service automatically |
| ECS | IAM Task Role | boto3 reads role credentials from environment |
| Lambda | IAM Execution Role | boto3 uses role automatically |
| Kubernetes | IRSA/Service Account | boto3 assumes role via OIDC |

The key: **boto3 automatically handles credential discovery** in the order listed above. You just need to make sure credentials are available somewhere in that chain!

## See Also

- [boto3 Credentials Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
- [AWS IAM Documentation](https://docs.aws.amazon.com/iam/)
- [AWS SDK for Python](https://aws.amazon.com/sdk-for-python/)