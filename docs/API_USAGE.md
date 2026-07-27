# Schema Registry API Usage Guide

FastAPI service that receives data contracts via HTTP API and uploads them to AWS Glue Schema Registry.

## Setup

### Prerequisites

- Python 3.10+
- AWS credentials configured (.env)
- Registry deployed via Terraform
- FastAPI and uvicorn installed

### Install Dependencies

```bash
pip install fastapi uvicorn boto3
```

### Start the Server

```bash
source .env
python app/main.py
```

Server starts at `http://localhost:8000`

Interactive API docs available at `http://localhost:8000/docs`

## API Endpoints

### 1. Health Check

**GET** `/`

Check service health.

**Response:**
```json
{
  "status": "healthy",
  "service": "Schema Registry Service",
  "version": "1.0.0"
}
```

### 2. Register Schema

**POST** `/api/v1/schemas/register`

Register a data contract to the schema registry.

**Request Body:**
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
      "description": "Email address"
    },
    {
      "name": "date_of_birth",
      "data_type": "date",
      "nullable": false,
      "description": "Date of birth"
    }
  ],
  "metadata": {
    "data_owner": "User Management",
    "data_owner_email": "user-mgmt@company.com",
    "data_steward": "Data Engineering",
    "data_steward_email": "data-eng@company.com",
    "sla_uptime_percentage": 99.95,
    "sla_max_latency_ms": 5000
  },
  "created_at": "2026-07-26T13:10:37.719833+00:00",
  "updated_at": "2026-07-26T13:10:37.719833+00:00"
}
```

**Query Parameters:**
- `registry_name` (optional): Registry name (default: "schema-registry")
- `schema_name` (optional): Custom schema name (default: contract_id)

**Response (201 Created):**
```json
{
  "success": true,
  "action": "created",
  "schema_name": "users-v1",
  "schema_arn": "arn:aws:glue:us-east-1:ACCOUNT:schema/schema-registry/users-v1",
  "version": 1,
  "registry_name": "schema-registry"
}
```

**Error Response (404):**
```json
{
  "detail": "Registry 'schema-registry' not found"
}
```

### 3. List Schemas

**GET** `/api/v1/schemas/list`

List all schemas in a registry.

**Query Parameters:**
- `registry_name` (optional): Registry name (default: "schema-registry")

**Response:**
```json
{
  "success": true,
  "registry_name": "schema-registry",
  "schema_count": 2,
  "schemas": [
    {
      "name": "users-v1",
      "latest_version": 1,
      "arn": "arn:aws:glue:us-east-1:ACCOUNT:schema/schema-registry/users-v1",
      "created_time": "2026-07-26 13:15:22.123456",
      "updated_time": "2026-07-26 13:15:22.123456"
    },
    {
      "name": "orders-v1",
      "latest_version": 2,
      "arn": "arn:aws:glue:us-east-1:ACCOUNT:schema/schema-registry/orders-v1",
      "created_time": "2026-07-26 12:00:00.000000",
      "updated_time": "2026-07-26 13:10:00.000000"
    }
  ]
}
```

### 4. Get Schema Details

**GET** `/api/v1/schemas/detail/{schema_name}`

Get details of a specific schema.

**Path Parameters:**
- `schema_name`: Name of the schema

**Query Parameters:**
- `registry_name` (optional): Registry name (default: "schema-registry")

**Response:**
```json
{
  "success": true,
  "schema_name": "users-v1",
  "schema_arn": "arn:aws:glue:us-east-1:ACCOUNT:schema/schema-registry/users-v1",
  "data_format": "AVRO",
  "compatibility": "BACKWARD",
  "description": "Schema for user records",
  "latest_version": 1,
  "created_time": "2026-07-26 13:15:22.123456",
  "updated_time": "2026-07-26 13:15:22.123456"
}
```

## Usage Examples

### Example 1: Register Schema from Generated Contract

```bash
# 1. Start server
source .env
python app/main.py

# 2. In another terminal, generate contract
python contracts_management/generate_contract.py

# 3. Upload via API
curl -X POST "http://localhost:8000/api/v1/schemas/register" \
  -H "Content-Type: application/json" \
  -d @contracts/user_contract.json
```

### Example 2: Using Python Requests

```python
import json
import requests

# Read contract
with open("../contracts/user/user_contract.json") as f:
    contract = json.load(f)

# Register schema
response = requests.post(
    "http://localhost:8000/api/v1/schemas/register",
    json=contract,
    params={
        "registry_name": "schema-registry",
        "schema_name": "user-schema"
    }
)

print(response.json())
# Output:
# {
#   "success": true,
#   "action": "created",
#   "schema_name": "user-schema",
#   "version": 1,
#   ...
# }
```

### Example 3: List All Schemas

```bash
curl "http://localhost:8000/api/v1/schemas/list?registry_name=schema-registry"
```

### Example 4: Get Schema Details

```bash
curl "http://localhost:8000/api/v1/schemas/detail/user-schema?registry_name=schema-registry"
```

### Example 5: Update Schema (Add New Version)

```bash
# Edit contracts/user_contract.json to add new fields

# Upload again (creates version 2)
curl -X POST "http://localhost:8000/api/v1/schemas/register" \
  -H "Content-Type: application/json" \
  -d @contracts/user_contract.json \
  -G -d "registry_name=schema-registry" \
  -G -d "schema_name=user-schema"
```

## Complete Workflow

```bash
# 1. Setup
source .env
cd infra/aws

# 2. Create infrastructure (registry only)
terraform init
terraform apply

# 3. Go back to project root
cd ../..

# 4. Start API server (in one terminal)
python app/main.py

# 5. Generate contract (in another terminal)
python contracts_management/generate_contract.py

# 6. Register schema via API
curl -X POST "http://localhost:8000/api/v1/schemas/register" \
  -H "Content-Type: application/json" \
  -d @contracts/user_contract.json

# 7. List schemas
curl "http://localhost:8000/api/v1/schemas/list"

# 8. Get schema details
curl "http://localhost:8000/api/v1/schemas/detail/users-v1"
```

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI where you can:
- Try all endpoints
- See request/response schemas
- Test with example data

## Error Handling

### Registry Not Found

**Status Code:** 404

```json
{
  "detail": "Registry 'schema-registry' not found"
}
```

**Solution:**
- Ensure Terraform has deployed the registry: `terraform apply`
- Check registry name is correct

### Schema Not Found

**Status Code:** 404

```json
{
  "detail": "Schema 'unknown-schema' not found in registry 'schema-registry'"
}
```

**Solution:**
- Register the schema first via POST /api/v1/schemas/register
- Check schema name is correct

### AWS Credentials Error

**Status Code:** 500

```json
{
  "detail": "Failed to register schema: Unable to locate credentials"
}
```

**Solution:**
- Ensure .env is sourced: `source .env`
- Check AWS credentials are valid
- Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set

### Schema Validation Failed

**Status Code:** 500

```json
{
  "detail": "Failed to register schema: Schema validation failed"
}
```

**Solution:**
- Check schema is valid AVRO format
- Verify compatibility with existing versions
- Review error message for specific issues

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Register Schema

on:
  push:
    paths:
      - 'contracts/**'
      - 'app/models.py'

jobs:
  register-schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Generate contract
        run: python contracts_management/generate_contract.py
      
      - name: Register schema
        run: |
          curl -X POST "http://schema-registry-api:8000/api/v1/schemas/register" \
            -H "Content-Type: application/json" \
            -d @contracts/user_contract.json
        env:
          SCHEMA_REGISTRY_URL: ${{ secrets.SCHEMA_REGISTRY_URL }}
```

## Performance Considerations

- Schema registration is fast (~1-2 seconds)
- List schemas can be slow with many schemas (100+)
- Consider caching schema lists in clients
- Use schema names as identifiers (not descriptions)

## Security

- Ensure API is behind authentication (not shown here)
- Restrict registry access to authorized users
- Audit all schema changes via CloudTrail
- Never expose registry name in client code

## Next Steps

1. Add authentication/authorization
2. Add request logging and monitoring
3. Add schema validation before upload
4. Add webhook notifications on schema changes
5. Integrate with data catalog (AWS Glue Data Catalog)