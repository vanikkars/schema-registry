# Upload Schemas to AWS Glue Schema Registry

Instead of hardcoding schemas in Terraform, use the Python API to upload contracts directly to the registry. This separates infrastructure from data contracts and provides more flexibility.

## Workflow

### Step 1: Create Infrastructure (Terraform)

```bash
source .env
cd infra/aws
terraform init
terraform plan
terraform apply
```

This creates only the **empty registry** (no schemas).

Output:
```
schema_registry_arn = "arn:aws:glue:us-east-1:ACCOUNT:registry/schema-registry"
schema_registry_name = "schema-registry"
```

### Step 2: Generate Data Contracts (Python)

```bash
cd /path/to/schema-registry
python contracts_management/generate_contract.py
```

Creates `contracts/user_contract.json` with:
- Column definitions
- Data types and nullability
- Metadata (owner, steward, SLAs)

### Step 3: Upload Schemas to Registry (Python)

#### Option 1: Upload single schema

```bash
source .env

python -m contracts_management.upload_to_glue upload \
  --registry schema-registry \
  --schema-name user-schema \
  --contract-file contracts/user_contract.json
```

Output:
```
✅ Found registry: schema-registry (ARN: arn:aws:glue:...)
📝 Creating new schema: user-schema
✅ Schema created: user-schema
   ARN: arn:aws:glue:us-east-1:ACCOUNT:schema/schema-registry/user-schema
   Version: 1
```

#### Option 2: List schemas in registry

```bash
python -m contracts_management.upload_to_glue list \
  --registry schema-registry
```

Output:
```
📋 Schemas in 'schema-registry':
  - user-schema (v1)
```

#### Option 3: Update schema (add new version)

Just run the upload command again with the updated contract file:

```bash
python -m contracts_management.upload_to_glue upload \
  --registry schema-registry \
  --schema-name user-schema \
  --contract-file contracts/user_contract.json
```

Creates version 2 with backward compatibility checking.

## Command Reference

### Upload Schema

```bash
python -m contracts_management.upload_to_glue upload \
  --registry REGISTRY_NAME \
  --schema-name SCHEMA_NAME \
  --contract-file PATH_TO_CONTRACT \
  [--format AVRO|PROTOBUF|JSON] \
  [--compatibility NONE|DISABLED|BACKWARD|FORWARD|BOTH] \
  [--region us-east-1]
```

**Options:**
- `--registry` - Glue registry name (default: schema-registry)
- `--schema-name` - Name for the schema in registry
- `--contract-file` - Path to contract JSON file (required)
- `--format` - Data format (default: AVRO)
- `--compatibility` - Compatibility mode (default: BACKWARD)
- `--region` - AWS region (default: us-east-1)

### List Schemas

```bash
python -m contracts_management.upload_to_glue list \
  --registry REGISTRY_NAME \
  [--region us-east-1]
```

## Complete Example Workflow

```bash
# 1. Setup
source .env
cd infra/aws

# 2. Deploy infrastructure (creates empty registry)
terraform init
terraform apply

# 3. View registry details
terraform output

# 4. Go back to project root
cd ../..

# 5. Generate contracts from models
python contracts_management/generate_contract.py

# 6. Upload contract to registry
python -m contracts_management.upload_to_glue upload \
  --registry schema-registry \
  --schema-name user-schema \
  --contract-file contracts/user_contract.json

# 7. Verify schema was uploaded
python -m contracts_management.upload_to_glue list \
  --registry schema-registry
```

## Benefits of API Upload vs Terraform

### Terraform Approach (Hardcoded):
- ❌ Schema changes require terraform apply
- ❌ Tightly coupled to infrastructure
- ❌ Schema versioning managed by Terraform state
- ✅ Everything in one place

### API Upload Approach (Flexible):
- ✅ Schema changes are independent from infrastructure
- ✅ Loosely coupled (infrastructure is separate)
- ✅ Schema versioning managed by AWS Glue
- ✅ Can upload multiple schemas without re-applying infrastructure
- ✅ Better for CI/CD pipelines (separate schema deployment step)
- ✅ Easy to update schemas independently

## Schema Evolution & Versioning

When you upload a schema again, Glue automatically:

1. **Validates compatibility** based on the `--compatibility` setting:
   - `BACKWARD` - New versions must be readable by old consumers
   - `FORWARD` - Old versions must be readable by new consumers
   - `BOTH` - Both directions
   - `NONE` - No checking (default for development)

2. **Creates new version** if validation passes:
   - Version 1 → Version 2 → Version 3, etc.
   - Previous versions remain available
   - Can roll back if needed

3. **Example:**

```bash
# Initial upload (creates v1)
python -m contracts_management.upload_to_glue upload \
  --registry schema-registry \
  --schema-name user-schema \
  --contract-file contracts/user_contract.json \
  --compatibility BACKWARD

# Later, update contract (creates v2)
# Edit contracts/user_contract.json to add new fields
python -m contracts_management.upload_to_glue upload \
  --registry schema-registry \
  --schema-name user-schema \
  --contract-file contracts/user_contract.json \
  --compatibility BACKWARD
```

## Python API Usage

You can also import and use the functions directly in your code:

```python
from contracts_management.upload_to_glue import upload_schema_to_registry

# Upload schema
response = upload_schema_to_registry(
    registry_name="schema-registry",
    schema_name="user-schema",
    schema_file=Path("contracts/user_contract.json"),
    data_format="AVRO",
    compatibility="BACKWARD",
    region="us-east-1",
)

print(f"Schema version: {response['VersionNumber']}")
```

## Troubleshooting

### "Registry not found"
Make sure Terraform has been applied to create the registry:
```bash
cd infra/aws
terraform apply
```

### "AccessDenied" error
Your IAM user needs these Glue permissions:
- `glue:GetRegistry`
- `glue:GetSchema`
- `glue:CreateSchema`
- `glue:PutSchemaVersion`

### Schema validation failed
Your new schema doesn't meet compatibility requirements. Check:
- Did you remove required fields? (breaks BACKWARD)
- Did you change field types? (may break compatibility)
- Use `--compatibility NONE` for testing