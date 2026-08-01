# Iceberg Table Creation Service

Dedicated service for creating and managing Iceberg tables in AWS Glue.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements-iceberg.txt

# Run the service
uvicorn iceberg_creation_service.app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Docker

```bash
# Start with docker-compose
docker-compose up -d iceberg-creation

# Test
curl http://localhost:8001/health
```

## API Endpoints

### Create Table

```bash
POST /api/v1/tables
Content-Type: application/json

{
  "contract_id": "users_v1",
  "name": "users",
  "version": 1,
  "columns": [
    {"name": "id", "data_type": "string"},
    {"name": "email", "data_type": "string"}
  ]
}
```

### Update Table Schema

```bash
POST /api/v1/tables/{table_name}/schema
```

### Get Table Info

```bash
GET /api/v1/tables/{table_name}
```

### Health Check

```bash
GET /health
```

## Architecture

```
app/main.py          → FastAPI routes
  ↓
application/use_cases.py  → Business logic
  ↓
domain/models.py         → Domain entities
domain/exceptions.py     → Exceptions
  ↓
adapters/aws_glue_adapter.py  → AWS integration
```

## Structure

- `app/` - FastAPI application
- `domain/` - Business models and exceptions
- `application/` - Use cases (business logic)
- `adapters/` - External service adapters (AWS Glue)
- `config.py` - Configuration