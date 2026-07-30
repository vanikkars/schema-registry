# Registry API

FastAPI service for managing data contracts in AWS Glue Schema Registry.

## Start the Server

```bash
# Option 1: Docker
docker-compose up

# Option 2: Direct uvicorn
python -m uvicorn registry_api.main:app --reload --host 0.0.0.0 --port 8000

# Option 3: Using script
bash run.sh
```

Server runs at `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /health
GET /
```

### Create Schema
```bash
POST /api/v1/schemas
Content-Type: application/json

# Body: DataContract JSON
```

**Response (201):**
```json
{
  "data": {
    "schema": { /* schema details */ },
    "table": { /* table info */ }
  }
}
```

### List Schemas
```bash
GET /api/v1/schemas
GET /api/v1/schemas?limit=20&offset=0
```

**Response:**
```json
{
  "data": [ /* list of schemas */ ],
  "meta": {
    "total": 10,
    "count": 20,
    "limit": 20,
    "offset": 0
  }
}
```

### Get Latest Schema
```bash
GET /api/v1/schemas/{schema_name}
```

**Response:**
```json
{
  "data": {
    "name": "users-v1",
    "latest_version": 5,
    "arn": "arn:aws:glue:...",
    "description": "...",
    "status": "AVAILABLE",
    "metadata": {
      "data_owner": "User Management",
      "data_steward": "Data Engineering",
      "sla_uptime_percentage": 99.95,
      "sla_max_latency_ms": 5000
    },
    "schema": { /* AVRO schema */ }
  }
}
```

### List All Versions
```bash
GET /api/v1/schemas/{schema_name}/versions
```

**Response:**
```json
{
  "data": {
    "schema_name": "users-v1",
    "latest_version": 5,
    "metadata": { /* schema metadata */ },
    "versions": [
      {
        "version": 1,
        "status": "AVAILABLE",
        "created_time": "2026-07-30T...",
        "schema": { /* AVRO schema */ }
      },
      {
        "version": 5,
        "status": "AVAILABLE",
        "created_time": "2026-07-30T...",
        "schema": { /* AVRO schema */ }
      }
    ]
  }
}
```

### Get Specific Version
```bash
GET /api/v1/schemas/{schema_name}/versions/{version}
```

**Response:**
```json
{
  "data": {
    "schema_name": "users-v1",
    "version": 5,
    "status": "AVAILABLE",
    "metadata": { /* schema metadata */ },
    "schema": { /* AVRO schema */ }
  }
}
```

## Examples

### Register Schema
```bash
curl -X POST "http://localhost:8000/api/v1/schemas" \
  -H "Content-Type: application/json" \
  -d @contracts/user/02/user_v1.json
```

### List All Versions
```bash
curl "http://localhost:8000/api/v1/schemas/users-v1/versions" | jq
```

### Get Specific Version
```bash
curl "http://localhost:8000/api/v1/schemas/users-v1/versions/5" | jq
```

## Python Client

```python
import requests
import json

# Register schema
with open("contracts/user/user_v1.json") as f:
    contract = json.load(f)

response = requests.post(
    "http://localhost:8000/api/v1/schemas",
    json=contract
)
print(response.json())

# Get latest version
response = requests.get("http://localhost:8000/api/v1/schemas/users-v1")
print(response.json()["data"]["metadata"])

# List all versions
response = requests.get("http://localhost:8000/api/v1/schemas/users-v1/versions")
versions = response.json()["data"]["versions"]
print(f"Total versions: {len(versions)}")
```

## Configuration

Environment variables (from `.env`):
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `AWS_DEFAULT_REGION` - AWS region (default: us-east-1)
- `TF_VAR_registry_name` - Registry name (default: schema-registry)

## Interactive Documentation

Visit `http://localhost:8000/docs` to:
- View all endpoints
- See request/response schemas
- Try endpoints with sample data

## Error Handling

| Status | Error |
|--------|-------|
| 404 | Schema or version not found |
| 400 | Invalid schema definition |
| 500 | AWS API error or internal error |

## Architecture

```
HTTP Request
    ↓
FastAPI Router (inbound)
    ↓
Use Cases (application)
    ↓
AWS Glue Adapter (outbound)
    ↓
AWS Glue API
```

### Key Components

- **router.py** - HTTP endpoints
- **use_cases.py** - Business logic
- **schema_registry_adapter.py** - AWS Glue integration
- **models.py** - Domain entities

## Troubleshooting

### Port 8000 in use
```bash
python -m uvicorn registry_api.main:app --port 8001
```

### AWS credentials error
```bash
# Ensure .env is sourced
source .env
python -m uvicorn registry_api.main:app --reload
```

### Module not found
```bash
# From project root
cd /path/to/schema-registry
source .env
python -m uvicorn registry_api.main:app --reload
```

## Dependencies

```
fastapi>=0.104.0
uvicorn>=0.24.0
boto3>=1.28.0
pydantic>=2.0.0
```

Install:
```bash
pip install -r requirements.txt
```
