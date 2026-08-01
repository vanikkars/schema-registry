# Iceberg Table Creation - Implementation Guide

This document explains how the Iceberg Table Creation Service is implemented and integrated with your schema registry.

## Architecture Overview

```
Schema Registry System (2 Independent Services)

┌─────────────────────────────────────────────┐
│     GitHub Actions Workflow                 │
│                                             │
│  Step 1: Schema Validation & Registration   │
│  ├─ Validate contract JSON                 │
│  ├─ POST /api/v1/schemas → Registry API    │
│  └─ Auto-merge if passed                   │
│                                             │
│  Step 2: Create Iceberg Tables             │
│  ├─ Read changed contract files            │
│  ├─ POST /api/v1/tables → Iceberg Service  │
│  └─ Report results to PR                   │
│                                             │
└────────────┬──────────────────────────────┘
             │
    ┌────────┴──────────┐
    ▼                   ▼
┌─────────────┐    ┌──────────────────┐
│  Schema     │    │  Iceberg Table   │
│  Registry   │    │  Creation        │
│  API        │    │  Service         │
│ Port: 8000  │    │  Port: 8001      │
└─────────────┘    └──────────────────┘
    │                   │
    └───────────┬───────┘
                ▼
         AWS Glue API
         (boto3)
```

## File Structure

```
schema-registry/
├── iceberg_creation_service/          # NEW: Iceberg Service
│   ├── __init__.py
│   ├── main.py                        # FastAPI app factory
│   ├── config.py                      # Configuration
│   ├── models.py                      # Pydantic models
│   ├── adapters.py                    # AWS Glue adapter
│   ├── exceptions.py                  # Custom exceptions
│   ├── routers/
│   │   ├── __init__.py
│   │   └── tables.py                  # Table endpoints
│   ├── Dockerfile
│   ├── README.md
│   └── requirements.txt
│
├── registry_api/                      # Existing: Schema Registry
│   ├── app/
│   ├── adapters/
│   ├── application/
│   ├── domain/
│   ├── Dockerfile
│   └── requirements.txt
│
├── .github/workflows/
│   ├── contract-validation-workflow.yml    # Existing
│   └── iceberg-table-creation.yml          # NEW
│
├── docker-compose.yml                 # Updated
├── requirements-iceberg.txt           # NEW: Iceberg deps
├── docs/
│   ├── ICEBERG_DEPLOYMENT.md         # NEW
│   └── ICEBERG_IMPLEMENTATION.md      # NEW (this file)
└── ...
```

## Key Components

### 1. Iceberg Service (Port 8001)

**Main Entry Point**: `iceberg_creation_service/main.py`

- Creates FastAPI application
- Includes health check endpoints
- Sets up exception handlers
- Returns pretty-formatted JSON

**Configuration**: `iceberg_creation_service/config.py`

- AWS region and database name
- Loaded from environment or `.env` file
- Settings pattern using Pydantic

**Data Models**: `iceberg_creation_service/models.py`

```python
# Request model
CreateTableRequest:
  - contract_id: Unique identifier
  - name: Human-readable name
  - version: Contract version
  - columns: List of Column objects
  - metadata: Optional ownership info
  - database_name: Override Glue database
  - s3_location: Override S3 path

# Response model
TableCreationResponse:
  - status: "created" | "exists" | "failed"
  - table_name: AWS Glue table name
  - database_name: Glue database
  - s3_location: S3 path for table data
  - message: Human-readable message
  - warnings: List of warnings
  - errors: List of errors
```

**AWS Adapter**: `iceberg_creation_service/adapters.py`

```python
GlueIcebergTableAdapter:
  - create_table(contract, database_name, s3_location)
    * Creates AWS Glue database if needed
    * Maps AVRO types to Glue types
    * Creates EXTERNAL_TABLE with ICEBERG parameters
    * Returns status and table details
    * Handles AlreadyExistsException

  - update_table_schema(contract, database_name)
    * Gets current table schema
    * Detects column changes (added, removed, modified)
    * Updates table with new schema
    * Returns detailed change list

  - get_table_info(table_name, database_name)
    * Retrieves table metadata
    * Returns column info and S3 location

  - _map_type_to_glue(avro_type)
    * Type conversion utility
    * Handles common AVRO types
```

**Router**: `iceberg_creation_service/routers/tables.py`

```python
POST /api/v1/tables
  ├─ Validate request body
  ├─ Call adapter.create_table()
  ├─ Handle errors with detailed messages
  └─ Return TableCreationResponse with status 201

POST /api/v1/tables/{table_name}/schema
  ├─ Update existing table schema
  ├─ Detect and report changes
  └─ Return update status

GET /api/v1/tables/{table_name}
  ├─ Retrieve table information
  └─ Return schema and metadata
```

### 2. GitHub Actions Workflow

**Workflow File**: `.github/workflows/iceberg-table-creation.yml`

Triggered after schema validation succeeds:

```yaml
on:
  workflow_run:
    workflows: ["Schema Validation & Auto-Merge"]
    types: [completed]
    branches: [main]
```

**Steps**:

1. **Checkout Code**
   - Checks out the merged PR branch
   - Full git history for file change detection

2. **Find Changed Files**
   - Detects contracts in `contracts/current/**/*.json`
   - Compares against `origin/main`
   - Uses git diff to find changes

3. **Create Iceberg Tables** (Main Step)
   - For each changed contract:
     - Reads JSON file
     - Validates structure
     - POST to Iceberg service
     - Collects response
   - Aggregates all results
   - Handles errors: timeout, connection, validation, AWS

4. **Post PR Comment**
   - Creates table with status for each contract
   - Shows success/failure indicators
   - Includes troubleshooting tips
   - Links to logs for debugging

### 3. Docker Setup

**Updated docker-compose.yml**:

```yaml
services:
  registry-api:        # Existing schema registry
    ports: 8000

  iceberg-creation:    # NEW Iceberg service
    ports: 8001
    depends_on: registry-api
    healthcheck: /health endpoint
    environment: AWS credentials
```

Both services can run independently but share the docker network.

## Data Flow

### Schema Registration + Table Creation

```
1. Developer pushes contract
2. GitHub PR created with change detection
3. Workflow triggered: "Schema Validation & Auto-Merge"
   ├─ Validates contract structure
   ├─ POST to Schema Registry API (:8000)
   ├─ Stores in AWS Glue Schema Registry
   └─ Auto-merges on success
4. Workflow triggered: "Create Iceberg Tables"
   ├─ Reads merged contract files
   ├─ For each contract:
   │   ├─ POST to Iceberg Service (:8001)
   │   ├─ Service creates table in AWS Glue
   │   └─ Returns result
   ├─ Aggregates all results
   └─ Comments on PR with results
5. User sees:
   ├─ Schema registration result
   └─ Table creation result (per contract)
```

### Request/Response Example

**Request to Iceberg Service**:

```json
POST /api/v1/tables
{
  "contract_id": "user_v1",
  "name": "user",
  "version": 1,
  "description": "User profile data",
  "columns": [
    {
      "name": "user_id",
      "data_type": "string",
      "description": "Unique identifier"
    },
    {
      "name": "email",
      "data_type": "string"
    }
  ],
  "metadata": {
    "data_owner": "platform-team",
    "data_steward": "jane@company.com"
  }
}
```

**Response from Iceberg Service**:

```json
HTTP 201 Created
{
  "data": {
    "status": "created",
    "table_name": "user_v1",
    "database_name": "iceberg_tables",
    "s3_location": "s3://iceberg-data-123456789-us-east-1/iceberg_tables/user_v1",
    "message": "Iceberg table 'user_v1' created successfully",
    "warnings": [],
    "errors": []
  }
}
```

## AWS Glue Integration

### Table Creation Process

1. **Database Check**
   - Attempts to create database "iceberg_tables"
   - Catches AlreadyExistsException (silent success)

2. **Type Mapping**
   - AVRO type → Glue type conversion
   - Default to "string" for unknown types
   - Preserves metadata (descriptions)

3. **Table Configuration**
   - Name: contract_id (normalized)
   - Type: EXTERNAL_TABLE
   - Format: IcebergInputFormat + IcebergOutputFormat
   - Serde: IcebergSerDe
   - Parameters: version, owner, steward, "table_type": ICEBERG

4. **S3 Location**
   - Auto-generated: `s3://iceberg-data-{account-id}-{region}/{db}/{table}`
   - Can be overridden in request

### Error Handling

```python
# AlreadyExistsException → status: "exists" (not a failure)
# TableCreationError → detailed error message
# Other exceptions → 500 Internal Server Error
```

## Deployment Architecture

### Development (docker-compose)

```
Local Machine
├── Schema Registry API :8000
├── Iceberg Service :8001
└── AWS Credentials from .env
```

### Production (Kubernetes)

```
Kubernetes Cluster
├── Deployment: iceberg-creation-service
│   ├── 2 replicas (configurable)
│   ├── Health checks (liveness + readiness)
│   ├── Resource limits (256Mi-512Mi)
│   └── IAM role for AWS access
├── Service: iceberg-creation-service
│   └── ClusterIP :8001 (internal)
└── Ingress/ALB: External HTTPS access
```

### GitHub Actions Integration

```
GitHub Actions Runner
├─ Environment: ubuntu-latest
├─ Network: Internet access (public IPs)
└─ Calls: https://iceberg-service-url/api/v1/tables
```

## Configuration

### Environment Variables

```env
# AWS (handled by IAM role in production)
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=***
AWS_SECRET_ACCESS_KEY=***

# Iceberg Service
ICEBERG_AWS_GLUE_DATABASE=iceberg_tables
ICEBERG_S3_BUCKET_PREFIX=iceberg-data
```

### GitHub Secrets

```
ICEBERG_SERVICE_URL=https://iceberg.example.com
```

## Type System & Validation

### Pydantic Models

- **CreateTableRequest**: Validates input contract
- **Column**: Validates individual column definition
- **Metadata**: Optional contract ownership info
- **TableCreationResponse**: Type-safe response

### Type Mapping

| AVRO | Glue | Notes |
|------|------|-------|
| string | string | |
| int | int | 32-bit |
| long | bigint | 64-bit |
| float | float | |
| double | double | |
| boolean | boolean | |
| bytes | binary | |
| date | date | |
| timestamp | timestamp | |

Unknown types default to "string".

## Error Handling Strategy

### Validation Errors

- **400 Bad Request**: Invalid contract schema
- **Example**: Missing required field "columns"

### AWS Errors

- **400 Bad Request**: Glue permission or API error
- **Example**: "Access Denied to Glue API"

### System Errors

- **500 Internal Server Error**: Unexpected system failure
- **Example**: AWS credential issue

All errors include:
- HTTP status code
- Human-readable message
- Error details for debugging

## Testing

### Local Testing

```bash
# Test health endpoint
curl http://localhost:8001/health

# Test table creation
curl -X POST http://localhost:8001/api/v1/tables \
  -H "Content-Type: application/json" \
  -d @contracts/current/user/user_v1.json

# Test table retrieval
curl http://localhost:8001/api/v1/tables/user_v1
```

### Integration Testing

```bash
# Start all services
docker-compose up -d

# Run workflow locally (using act)
act -j create-iceberg-tables -s ICEBERG_SERVICE_URL=http://localhost:8001

# Check results
curl http://localhost:8001/api/v1/tables/user_v1
```

## Monitoring & Logging

### Logs

- **Source**: Service stdout (Docker/K8s)
- **Format**: Structured with timestamps
- **Levels**: INFO, ERROR
- **Key Events**:
  - Table creation started
  - Table creation completed
  - Errors with stack traces

### Observability

- Health check: `/health` → `{"status": "ok"}`
- Liveness probe: HTTP GET /health
- Readiness probe: HTTP GET /health
- Error responses: Detailed error messages

## Scaling & Performance

### Horizontal Scaling

Service is stateless, can scale horizontally:

- **Kubernetes**: Increase replicas
- **ECS**: Increase desired count
- **Load Balancer**: Distribute requests

### Performance Metrics

- Single request: ~500ms-2s (includes AWS Glue API)
- Concurrent: Can handle ~10-20 concurrent requests
- Typical PR: 5-10 tables, ~15-30s total

### Cost Optimization

- Run on-demand (not always active)
- Small memory footprint (256MB-512MB)
- Minimal AWS API calls (only Glue + STS)
- No data transfer costs (internal AWS)

## Future Enhancements

Possible improvements:

1. **Async Processing**
   - Return request ID immediately
   - Poll for status later
   - Useful for high volume

2. **Batch Operations**
   - Create multiple tables in one request
   - Parallel processing

3. **Schema Versioning**
   - Keep table schema versions
   - Easy rollback to previous version

4. **Metrics & Observability**
   - Prometheus metrics
   - CloudWatch integration
   - Request timing

5. **Advanced Schema Evolution**
   - Automatic column reordering
   - Type promotions (int → long)
   - Constraint management

## Related Files

- [Architecture Overview](./ARCHITECTURE.md)
- [Deployment Guide](./ICEBERG_DEPLOYMENT.md)
- [Service README](../iceberg_creation_service/README.md)
- [GitHub Workflows](.github/workflows/)