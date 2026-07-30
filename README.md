# Schema Registry API

A FastAPI-based data contract management system with AWS Glue Schema Registry integration.

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with AWS credentials
source .env
```

### 2. Deploy Infrastructure (Terraform)

```bash
cd infra/aws
terraform init
terraform plan
terraform apply
```

### 3. Start the API

```bash
docker-compose up
# or
python -m uvicorn registry_api.main:app --reload
```

API runs at `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /health
```

### Create Schema
```bash
POST /api/v1/schemas
Content-Type: application/json

# Request body: data contract JSON
```

### List All Schemas
```bash
GET /api/v1/schemas?limit=20&offset=0
```

### Get Latest Schema
```bash
GET /api/v1/schemas/{schema_name}
```

Returns latest version with metadata (owner, steward, SLAs, etc.)

### List All Versions
```bash
GET /api/v1/schemas/{schema_name}/versions
```

Returns list of all available versions with metadata and schema definitions.

### Get Specific Version
```bash
GET /api/v1/schemas/{schema_name}/versions/{version}
```

Returns specific version with metadata and full schema definition.

## Example Usage

### Register a Schema

```bash
curl -X POST "http://localhost:8000/api/v1/schemas" \
  -H "Content-Type: application/json" \
  -d @contracts/user/02/user_v1.json
```

### Get Latest Version with Metadata

```bash
curl "http://localhost:8000/api/v1/schemas/users-v1" | jq '.data'
```

### List All Versions

```bash
curl "http://localhost:8000/api/v1/schemas/users-v1/versions" | jq '.data.versions'
```

### Get Specific Version

```bash
curl "http://localhost:8000/api/v1/schemas/users-v1/versions/5" | jq '.data'
```

## Project Structure

```
schema-registry/
├── registry_api/              # FastAPI application
│   ├── domain/               # Business logic
│   ├── application/          # Use cases
│   ├── adapters/             # AWS integration
│   └── main.py              # Entry point
├── contracts/                # Data contract definitions
├── infra/                    # Terraform IaC
│   └── aws/                 # AWS resources
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Architecture

### Layers

- **Domain**: Data models, entities, business rules
- **Application**: Use cases, orchestration
- **Adapters**: AWS Glue integration, HTTP API
- **Infrastructure**: Docker, Terraform, AWS

### Key Features

- ✅ Schema registration and versioning
- ✅ Metadata tracking (owner, steward, SLAs)
- ✅ AVRO schema generation and validation
- ✅ Backward compatibility checking
- ✅ Multi-version support
- ✅ Interactive API documentation (Swagger)

## Environment Variables

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1

# Glue Registry
TF_VAR_registry_name=schema-registry
TF_VAR_registry_description=Schema Registry for data contracts
```

## Requirements

- Python 3.10+
- Terraform >= 1.0
- AWS Account with Glue permissions
- Docker (optional)

## Documentation

- [Registry API](registry_api/README.md) - API details
- [Infrastructure](infra/README.md) - Terraform setup
- [AWS Setup](infra/aws/README.md) - AWS configuration

## License

MIT
