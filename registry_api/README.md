# Registry API

FastAPI service for managing data contracts in AWS Glue Schema Registry.

## Overview

REST API that receives data contracts and uploads them to AWS Glue Schema Registry. Provides schema management, versioning, and compatibility checking.

## Features

- ✅ Register data contracts as schemas
- ✅ List schemas in a registry
- ✅ Get schema details and history
- ✅ Automatic AVRO schema conversion
- ✅ Schema versioning with compatibility checking
- ✅ Interactive Swagger UI
- ✅ Health check endpoints

## Quick Start

### 1. Setup Environment

```bash
# From project root
source .env
```

### 2. Start the Server

```bash
# Option 1: Using helper script
bash registry-api/run.sh

# Option 2: Direct uvicorn
python -m uvicorn registry_api.main:app --reload --host 0.0.0.0 --port 8000

# Option 3: Using main.py
python registry_api/main.py
```

Server runs at `http://localhost:8000`

### 3. Access API

**Interactive API Documentation:**
```
http://localhost:8000/docs
```

**Health Check:**
```bash
curl http://localhost:8000/
```

## API Endpoints

### Health Check

```
GET /
GET /health
```

Returns service status.

### Register Schema

```
POST /api/v1/schemas/register
```

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
      "description": "Username"
    },
    {
      "name": "email",
      "data_type": "string",
      "nullable": false,
      "description": "Email address"
    }
  ],
  "metadata": {
    "data_owner": "User Management",
    "data_owner_email": "owner@company.com",
    "data_steward": "Data Engineering",
    "data_steward_email": "eng@company.com",
    "sla_uptime_percentage": 99.95,
    "sla_max_latency_ms": 5000
  },
  "created_at": "2026-07-26T13:10:37.719833+00:00",
  "updated_at": "2026-07-26T13:10:37.719833+00:00"
}
```

**Query Parameters:**
- `registry_name` (optional): Registry name (default: "schema-registry")
- `schema_name` (optional): Custom schema name

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

### List Schemas

```
GET /api/v1/schemas/list?registry_name=schema-registry
```

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
    }
  ]
}
```

### Get Schema Details

```
GET /api/v1/schemas/detail/{schema_name}?registry_name=schema-registry
```

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

### Example 1: Register Contract via cURL

```bash
# Generate contract first
python contracts_management/generate_contract.py

# Register schema
curl -X POST "http://localhost:8000/api/v1/schemas/register" \
  -H "Content-Type: application/json" \
  -d @contracts/user_contract.json
```

### Example 2: Register Contract via Python

```python
import json
import requests

# Load contract
with open("contracts/user_contract.json") as f:
    contract = json.load(f)

# Register schema
response = requests.post(
    "http://localhost:8000/api/v1/schemas/register",
    json=contract,
    params={"registry_name": "schema-registry"}
)

print(response.json())
```

### Example 3: List All Schemas

```bash
curl "http://localhost:8000/api/v1/schemas/list"
```

### Example 4: Get Schema Details

```bash
curl "http://localhost:8000/api/v1/schemas/detail/users-v1"
```

### Example 5: Update Schema (Add New Version)

```bash
# Edit contracts/user_contract.json with new fields

# Register again (creates version 2)
curl -X POST "http://localhost:8000/api/v1/schemas/register" \
  -H "Content-Type: application/json" \
  -d @contracts/user_contract.json
```

## File Structure

```
registry-api/
├── __init__.py      # Package initialization
├── main.py          # FastAPI application
├── api.py           # API endpoints and client
├── run.sh           # Start script
└── README.md        # This file
```

## Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `boto3` - AWS SDK
- `pydantic` - Data validation

Install with:
```bash
pip install fastapi uvicorn boto3 pydantic
```

## Configuration

Environment variables (from `.env`):
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `AWS_DEFAULT_REGION` - AWS region (default: us-east-1)

## Interactive API Documentation

Visit `http://localhost:8000/docs` to:
- View all endpoints
- See request/response schemas
- Try endpoints with sample data
- View parameter descriptions

## Error Handling

### Registry Not Found (404)
```json
{
  "detail": "Registry 'schema-registry' not found"
}
```

### Schema Not Found (404)
```json
{
  "detail": "Schema 'unknown' not found in registry 'schema-registry'"
}
```

### AWS Credentials Error (500)
```json
{
  "detail": "Failed to register schema: Unable to locate credentials"
}
```

**Solutions:**
- Ensure `.env` is sourced: `source .env`
- Check AWS credentials are valid
- Verify registry exists (created by Terraform)

## Performance

- Schema registration: ~1-2 seconds
- List schemas: ~500ms-1s
- Get schema details: ~500ms

## Monitoring

The API logs all requests and errors. Monitor:
- Request latency
- Error rates
- AWS API call counts
- Schema registration metrics

## Security Considerations

⚠️ **Important:**
- Add authentication before production use
- Restrict registry access to authorized users
- Enable CloudTrail for audit logging
- Never expose credentials in requests
- Use HTTPS in production

## Integration with CI/CD

Example GitHub Actions workflow:

```yaml
- name: Register Schema
  run: |
    curl -X POST "http://schema-registry-api:8000/api/v1/schemas/register" \
      -H "Content-Type: application/json" \
      -d @contracts/user_contract.json
```

## Troubleshooting

### Port 8000 Already in Use

```bash
# Use a different port
python -m uvicorn registry_api.main:app --port 8001
```

### AWS Credentials Not Found

```bash
# Make sure to source .env first
source .env
bash registry-api/run.sh
```

### Module Not Found

```bash
# Make sure you're in the project root
cd /path/to/schema-registry
source .env
bash registry-api/run.sh
```

## Next Steps

1. Add authentication (API keys, OAuth2)
2. Add request logging and metrics
3. Add schema validation before upload
4. Add webhook notifications
5. Integrate with monitoring/alerting
6. Add rate limiting
7. Add request caching

## See Also

- [API_USAGE.md](../docs/API_USAGE.md) - Complete API documentation
- [README.md](../) - Main project documentation
- [UPLOAD_SCHEMAS.md](../docs/UPLOAD_SCHEMAS.md) - Schema upload guide