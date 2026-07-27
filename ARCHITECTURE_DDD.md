# Schema Registry API - Domain-Driven Design Architecture

## Overview

The `registry_api` FastAPI service has been refactored to follow **Domain-Driven Design (DDD)** principles and **Hexagonal Architecture** (ports & adapters), separating concerns across four layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP / FastAPI                            │
│              (Driving Adapter - Inbound)                     │
├─────────────────────────────────────────────────────────────┤
│                 Application Layer (Use Cases)                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ RegisterSchemaUseCase, ListSchemasUseCase, etc.        │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────┬───────────────────────────────────────┤
│   Domain Layer       │      Application Ports (Interfaces)    │
│ ┌────────────────┐   │  ┌───────────────────────────────┐    │
│ │ DataContract   │   │  │ SchemaRegistryPort            │    │
│ │ Column         │───┼──┤ TableCatalogPort              │    │
│ │ Metadata       │   │  └───────────────────────────────┘    │
│ │ Exceptions     │   │                                        │
│ └────────────────┘   │                                        │
├─────────────────────┴───────────────────────────────────────┤
│           Infrastructure / Adapters (Driven)                 │
│  ┌──────────────────────┐      ┌─────────────────────────┐  │
│  │ Glue Schema Registry │      │ Glue Iceberg Table      │  │
│  │ Adapter              │      │ Adapter                 │  │
│  │ (boto3 calls)        │      │ (boto3 calls)           │  │
│  └──────────────────────┘      └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│              External Systems (AWS Glue, S3)                 │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. Domain Layer (`registry_api/domain/`)

**Purpose**: Contains core business logic and entities, completely independent of frameworks and external systems.

**Files**:
- `models.py`: Pydantic entities
  - `DataContract`: Main domain entity representing a data schema contract
  - `ColumnDefinition`: Value object for column metadata
  - `ContractMetadata`: Value object for contract governance info
  
- `exceptions.py`: Typed domain errors
  - `SchemaRegistryError`: Base exception
  - `RegistryNotFoundError`: Registry doesn't exist
  - `SchemaNotFoundError`: Schema doesn't exist
  - `InvalidVersionError`: Invalid version format
  - `VersionNotFoundError`: Version doesn't exist
  - `TableCreationError`: Table creation failed

**Key principle**: No imports from FastAPI, boto3, or adapter code. Pure business rules.

### 2. Application Layer (`registry_api/application/`)

**Purpose**: Orchestrates domain entities through use cases, defines abstract ports that adapters must implement.

**Files**:
- `ports.py`: Abstract interfaces (ABC)
  - `SchemaRegistryPort`: Interface for registry operations
    - `register_schema(contract) → str (arn)`
    - `get_schema(name) → dict | None`
    - `list_schemas() → list`
    - `get_schema_versions(name) → dict | None`
  
  - `TableCatalogPort`: Interface for table catalog operations
    - `create_table(contract, ...) → dict`

- `use_cases.py`: Orchestrators per business operation
  - `RegisterSchemaUseCase`: Register contract, create table
  - `ListSchemasUseCase`: List all schemas with pagination
  - `GetSchemaUseCase`: Get single schema details
  - `GetSchemaVersionsUseCase`: Get schema version info
  - `GetSchemaVersionUseCase`: Get specific version
  - `DeleteSchemaUseCase`: Delete schema (placeholder)

**Key principle**: Use cases receive ports in constructor (dependency injection). They orchestrate domain logic and delegate to ports. They raise typed domain exceptions, which adapters translate to appropriate responses.

### 3. Adapters Layer

#### Inbound Adapter: HTTP (`registry_api/adapters/inbound/http/`)

**Purpose**: Translates HTTP requests into use case calls, domain exceptions to HTTP status codes.

**Files**:
- `router.py`: FastAPI endpoints
  - `POST /api/v1/schemas` → `RegisterSchemaUseCase`
  - `GET /api/v1/schemas` → `ListSchemasUseCase`
  - `GET /api/v1/schemas/{name}` → `GetSchemaUseCase`
  - `GET /api/v1/schemas/{name}/versions` → `GetSchemaVersionsUseCase`
  - `GET /api/v1/schemas/{name}/versions/{version}` → `GetSchemaVersionUseCase`
  - `DELETE /api/v1/schemas/{name}` → `DeleteSchemaUseCase`

- `dto.py`: Response formatting helpers

**Exception mapping**:
- `SchemaNotFoundError` → 404 Not Found
- `InvalidVersionError` → 400 Bad Request
- `VersionNotFoundError` → 404 Not Found
- `RegistryNotFoundError` → 400 Bad Request
- Other `SchemaRegistryError` → 500 Internal Server Error

#### Outbound Adapter: AWS Glue (`registry_api/adapters/outbound/aws_glue/`)

**Purpose**: Implements port interfaces using boto3, handles AWS-specific logic.

**Files**:
- `schema_registry_adapter.py`: `GlueSchemaRegistryAdapter` implements `SchemaRegistryPort`
  - Uses `boto3.client("glue")` to interact with AWS Glue Schema Registry
  - Handles registry existence checks, schema CRUD operations
  
- `table_catalog_adapter.py`: `GlueIcebergTableAdapter` implements `TableCatalogPort`
  - Uses `boto3.client("glue")` for Iceberg table creation
  - Auto-generates S3 locations, handles table existence

- `mappers.py`: AWS-specific type conversion utilities (not domain logic)
  - `contract_to_avro(contract) → str`: DataContract → AVRO schema JSON
  - `map_type_to_glue(type) → str`: Type mapping for Glue/Hive
  - `map_type_to_avro(type) → str`: Type mapping for AVRO

**Key principle**: Adapters only understand AWS SDK and port contracts. They don't know about HTTP, FastAPI, or other adapters.

### 4. Composition Root (`registry_api/app/main.py`)

**Purpose**: Wires together all layers — instantiates concrete adapters, injects them into use cases, mounts routers.

**Key code pattern**:
```python
# Instantiate adapters
schema_registry = GlueSchemaRegistryAdapter()
table_catalog = GlueIcebergTableAdapter()

# Inject adapters into use cases
register_use_case = RegisterSchemaUseCase(
    schema_registry=schema_registry,
    table_catalog=table_catalog
)

# Create router with use cases
router = create_router(
    register_schema_use_case=register_use_case,
    ...
)

# Mount in FastAPI app
app.include_router(router)
```

**Important**: Maintains `registry_api.app.main:app` import path for Docker/uvicorn.

## Request Flow Example

**POST /api/v1/schemas** with a DataContract JSON body:

```
HTTP Request
    ↓
router.create_schema(contract: DataContract)  [inbound adapter]
    ↓
register_use_case.execute(contract)  [application layer]
    ├─→ schema_registry.register_schema(contract)  [outbound adapter → AWS]
    └─→ table_catalog.create_table(contract)  [outbound adapter → AWS]
    ↓
    ├─ On success: returns {"data": {"schema": ..., "table": ...}}
    └─ On SchemaNotFoundError: raises → caught by router → 404
    ↓
HTTP Response (201 Created or 4xx/5xx error)
```

## Benefits

✅ **Testability**: Mock adapters, test use cases in isolation
✅ **Flexibility**: Swap AWS Glue for another registry (Mock, Kafka, etc.) by implementing new adapters
✅ **Maintainability**: Clear boundaries between domain logic, orchestration, and infrastructure
✅ **Extensibility**: Add new use cases without changing adapters
✅ **Traceability**: Domain errors explicitly propagate up the stack

## No Breaking Changes

- All 5 REST endpoints, paths, and response formats remain identical
- Status codes and error responses match the previous behavior
- AWS Glue integration unchanged (same boto3 calls)
- Configuration via environment variables (AWS_DEFAULT_REGION, TF_VAR_registry_name)

## Running the Service

**Docker**:
```bash
docker build -f registry_api/Dockerfile -t schema-registry .
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=... \
  -e AWS_SECRET_ACCESS_KEY=... \
  schema-registry
```

**Local (with dependencies)**:
```bash
source .venv/bin/activate
python -m uvicorn registry_api.app.main:app --reload
```

**Health check**:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI
```
