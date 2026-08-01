# Schema Registry

A FastAPI-based data contract management system with AWS Glue integration and GitHub Actions automation.

## Quick Start

```bash
# Setup environment
cp .env.example .env
source .env

# Start services
docker-compose up

# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Services

- **Registry API** (8000) - Schema management and contracts
- **Iceberg Service** (8001) - Table creation and management

## Key Endpoints

```
GET    /health                              Service health
POST   /api/v1/schemas                      Register schema
GET    /api/v1/schemas                      List schemas
GET    /api/v1/schemas/{name}               Get latest schema
GET    /api/v1/schemas/{name}/versions      List versions
GET    /api/v1/schemas/{name}/versions/{v}  Get specific version
```

## GitHub Actions Integration

Schemas in `contracts/current/` trigger automated workflows:
1. **Validate** - Schema validation via Registry API
2. **Create Tables** - Iceberg table creation via Iceberg Service

Set GitHub secrets for local testing:
- `REGISTRY_API_URL` - Local or tunnel URL
- `ICEBERG_SERVICE_URL` - Local or tunnel URL

## Expose Services to GitHub Actions

```bash
# Option 1: Direct localhost (same machine)
# Set secrets to http://localhost:8000 and http://localhost:8001

# Option 2: Cloudflare Tunnel
cloudflared tunnel --url http://127.0.0.1:8000  # Terminal 2a
cloudflared tunnel --url http://127.0.0.1:8001  # Terminal 2b
# Set secrets to generated URLs
```

## Architecture

```
registry_api/           Domain-driven design with layers:
├── domain/            Business logic & entities
├── application/       Use cases & orchestration
├── adapters/          AWS Glue integration
└── main.py           FastAPI entry point

iceberg_creation_service/  Table management:
├── domain/            Business logic
├── application/       Use cases
├── adapters/          AWS Glue integration
└── main.py           FastAPI entry point

contracts/             Schema definitions
infra/                 Terraform & AWS setup
```

## Environment Variables

```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
REGISTRY_API_URL=http://localhost:8000
ICEBERG_SERVICE_URL=http://localhost:8001
```

## Requirements

- Python 3.10+
- Docker & Docker Compose
- AWS Account (for production)
- Terraform >= 1.0 (for infrastructure)

## Documentation

- [Registry API](registry_api/README.md)
- [Iceberg Service](iceberg_creation_service/README.md)
- [Contracts](contracts/README.md)
- [Infrastructure](infra/README.md)

## Commands

```bash
make docker-up              # Start services
make docker-down            # Stop services
make tunnel-run-registry    # Expose Registry API via tunnel
make tunnel-run-iceberg     # Expose Iceberg Service via tunnel
make tunnel-stop            # Stop tunnels
```
