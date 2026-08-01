# Iceberg Table Creation Service

A dedicated HTTP service for creating and managing Iceberg tables in AWS Glue. This service is decoupled from the schema registry to allow independent deployment, scaling, and retry mechanisms.

## Overview

The Iceberg Table Creation Service provides a REST API for:
- Creating new Iceberg tables from data contracts
- Updating table schemas as contracts evolve
- Retrieving table information

## Architecture

```
GitHub Actions Workflow
    ├─ Step 1: Schema Validation & Registration
    │   └─ POST /api/v1/schemas → Schema Registry API (port 8000)
    │
    └─ Step 2: Iceberg Table Creation
        └─ POST /api/v1/tables → Iceberg Creation Service (port 8001)
```

## Endpoints

### Create Table

```http
POST /api/v1/tables
Content-Type: application/json

{
  "contract_id": "user_v1",
  "name": "user",
  "version": 1,
  "description": "User data contract",
  "columns": [
    {
      "name": "user_id",
      "data_type": "string",
      "description": "Unique user ID"
    },
    {
      "name": "email",
      "data_type": "string"
    }
  ],
  "metadata": {
    "data_owner": "data-team",
    "data_steward": "john.doe@company.com"
  }
}
```

**Response (201 Created):**

```json
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

### Update Table Schema

```http
POST /api/v1/tables/{table_name}/schema
Content-Type: application/json

{
  "contract_id": "user_v2",
  "name": "user",
  "version": 2,
  "columns": [...]
}
```

### Get Table Info

```http
GET /api/v1/tables/{table_name}
```

### Health Check

```http
GET /health
```

## Local Development

### Prerequisites

- Python 3.11+
- AWS credentials configured (via environment variables or AWS profile)
- Docker (optional, for containerized setup)

### Installation

```bash
# Install dependencies
pip install -r requirements-iceberg.txt

# Or use uv (if available)
uv pip install -r requirements-iceberg.txt
```

### Running the Service

```bash
# Using uvicorn directly
uvicorn iceberg_creation_service.main:app --host 0.0.0.0 --port 8001 --reload

# Using the module
python -m uvicorn iceberg_creation_service.main:app --host 0.0.0.0 --port 8001 --reload

# Using docker-compose (with both services)
docker-compose up -d
```

The service will be available at `http://localhost:8001`

### Testing

```bash
# Test the health endpoint
curl http://localhost:8001/health

# Test table creation
curl -X POST http://localhost:8001/api/v1/tables \
  -H "Content-Type: application/json" \
  -d @contracts/current/user/user_v1.json
```

## Environment Variables

```env
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Service Configuration
ICEBERG_AWS_GLUE_DATABASE=iceberg_tables
ICEBERG_S3_BUCKET_PREFIX=iceberg-data
```

## Data Flow

1. **Contract Arrives** - Data contract from GitHub Actions
2. **Validation** - Contract schema is validated
3. **Table Creation** - AWS Glue Iceberg table is created
4. **Response** - Success/failure with details returned to workflow
5. **Feedback** - PR comment posted with results

## Error Handling

The service returns detailed error messages:

- **400 Bad Request** - Invalid contract or missing required fields
- **404 Not Found** - Table does not exist
- **500 Internal Server Error** - AWS/system errors

Example error response:

```json
{
  "detail": "Table creation failed: Access Denied to Glue API"
}
```

## Deployment

### Docker

```bash
# Build the image
docker build -f iceberg_creation_service/Dockerfile -t iceberg-creation-service:1.0 .

# Run the container
docker run -p 8001:8001 \
  -e AWS_ACCESS_KEY_ID=your-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret \
  -e AWS_DEFAULT_REGION=us-east-1 \
  iceberg-creation-service:1.0
```

### Docker Compose

```bash
docker-compose up -d iceberg-creation
```

### Kubernetes

```bash
kubectl apply -f deploy/iceberg-service.yaml
```

### AWS ECS Fargate

See `infra/aws/ecs/` for Terraform configuration.

## Monitoring

### Logs

The service logs to stdout. In Docker/Kubernetes environments, use:

```bash
# Docker
docker logs iceberg-creation-service

# Kubernetes
kubectl logs -f deployment/iceberg-creation-service
```

### Health Check

The service exposes `/health` endpoint that returns:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### Metrics

Logs include:
- Table creation events
- Schema updates
- Errors with stack traces

## Type Mapping

The service maps AVRO types to AWS Glue types:

| AVRO Type | Glue Type |
|-----------|-----------|
| string    | string    |
| int       | int       |
| long      | bigint    |
| float     | float     |
| double    | double    |
| boolean   | boolean   |
| bytes     | binary    |
| date      | date      |
| timestamp | timestamp |

## Troubleshooting

### Service won't start

1. Check AWS credentials are configured
2. Verify Python version is 3.11+
3. Check port 8001 is not in use
4. Review logs for error details

### Table creation fails

1. Verify AWS Glue permissions
2. Check contract schema is valid
3. Ensure S3 bucket exists (or service has permissions to create it)
4. Review AWS Glue error messages in logs

### Connection errors from GitHub Actions

1. Verify `ICEBERG_SERVICE_URL` secret is set correctly
2. Check service is accessible from GitHub (firewall/security groups)
3. Ensure service is running and healthy

## Architecture Decisions

### Why a Separate Service?

- **Decoupling** - Schema registration and table creation can be updated independently
- **Scalability** - Can scale independently based on table creation load
- **Reusability** - Can be called from multiple sources (not just GitHub)
- **Clarity** - Clear separation of concerns
- **Resilience** - Failures in table creation don't affect schema registration

### Why Synchronous?

- **User Feedback** - GitHub Actions can report results immediately in PR comments
- **Simplicity** - No need for polling or async handling
- **Reliability** - Direct error reporting and traceability

## Contributing

When modifying this service:

1. Follow the existing code structure
2. Add type hints to all functions
3. Update tests and documentation
4. Follow PEP 8 style guidelines

## Related Documentation

- [Hybrid Architecture Guide](../../docs/ICEBERG_ARCHITECTURE.md)
- [GitHub Actions Workflows](.github/workflows/)
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)