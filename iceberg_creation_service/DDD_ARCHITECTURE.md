# Iceberg Service - Domain-Driven Design Architecture

## Overview

The Iceberg Table Creation Service has been refactored using **Domain-Driven Design (DDD)** principles to create a clean, maintainable, and scalable architecture.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│          Presentation Layer (FastAPI)                   │
│  ├─ presentation/routes.py                              │
│  └─ HTTP endpoints with error handling                  │
└──────────────────────┬──────────────────────────────────┘
                       │ (DTOs)
┌──────────────────────▼──────────────────────────────────┐
│        Application Layer (Use Cases)                     │
│  ├─ application/use_cases.py                            │
│  ├─ application/dto.py                                  │
│  └─ Orchestrates business operations                    │
└──────────────────────┬──────────────────────────────────┘
                       │ (Domain Entities)
┌──────────────────────▼──────────────────────────────────┐
│            Domain Layer (Business Logic)                │
│  ├─ domain/entities.py                                  │
│  ├─ domain/value_objects.py                             │
│  ├─ domain/repositories.py (interface)                  │
│  ├─ domain/exceptions.py                                │
│  └─ Pure business logic (no infrastructure)             │
└──────────────────────┬──────────────────────────────────┘
                       │ (Repository Implementation)
┌──────────────────────▼──────────────────────────────────┐
│       Infrastructure Layer (External Services)          │
│  ├─ infrastructure/repositories.py                      │
│  └─ AWS Glue adapter implementation                     │
└─────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. Domain Layer (Core Business Logic)

**Location**: `domain/`

The heart of the application. Contains pure business logic with no dependencies on external frameworks.

#### Entities (`domain/entities.py`)
- **IcebergTable**: Aggregate root representing an Iceberg table
  - Encapsulates table properties and business rules
  - Validates data through `validate()` method
  - Manages schema evolution through `update_schema()`
  - Tracks status through value objects

- **SchemaEvolution**: Value object capturing schema changes
  - Detects added/removed/modified columns
  - Provides warnings for risky changes
  - Generates change summaries for reporting

#### Value Objects (`domain/value_objects.py`)
Immutable, self-validating objects with no identity:

- **TableName**: Validates and normalizes table names
- **ContractId**: Immutable contract identifier
- **Version**: Semantic versioning (major.minor.patch)
- **Column**: Table column definition with type validation
- **DatabaseName**: Database identifier
- **S3Location**: S3 path with validation
- **TableMetadata**: Ownership and stewardship info
- **TableStatus**: Table status enumeration
- **DataType**: AVRO type mapping to Glue types

**Key Benefits**:
- Type safety without nullable types
- Business rule validation at construction time
- Immutability prevents accidental mutations
- Reusable across the codebase

#### Repository Interface (`domain/repositories.py`)
Abstract interface for data persistence:

```python
class IcebergTableRepository(ABC):
    async def save(table: IcebergTable) -> None
    async def get_by_name(table_name: TableName) -> Optional[IcebergTable]
    async def exists(table_name: TableName) -> bool
    async def update(table: IcebergTable) -> None
    async def create_database_if_not_exists(database_name: str) -> None
```

Allows swapping implementations without changing business logic.

#### Domain Exceptions (`domain/exceptions.py`)
Business-level errors:
- `TableCreationError`: Table creation failed
- `TableNotFoundError`: Table does not exist
- `InvalidTableError`: Table data is invalid
- `SchemaEvolutionError`: Schema evolution rules violated
- `InvalidDataTypeError`: Unsupported data type

### 2. Application Layer (Use Cases)

**Location**: `application/`

Orchestrates domain entities and repositories to implement user stories.

#### Use Cases (`application/use_cases.py`)

**CreateTableUseCase**
```python
async def execute(input_dto: CreateTableInputDto) -> CreateTableOutputDto:
    1. Validate input
    2. Build domain entities from input
    3. Check business rules
    4. Persist using repository
    5. Return results
```

**UpdateTableSchemaUseCase**
```python
async def execute(input_dto: UpdateTableSchemaInputDto) -> UpdateTableSchemaOutputDto:
    1. Load existing table
    2. Build new columns
    3. Detect schema evolution
    4. Apply changes
    5. Persist and report
```

**GetTableInfoUseCase**
```python
async def execute(table_name: str) -> GetTableInfoOutputDto:
    1. Fetch table from repository
    2. Transform to output format
    3. Return info
```

#### DTOs (`application/dto.py`)
Data Transfer Objects for API boundaries:

**Input DTOs**:
- `CreateTableInputDto`: Request to create table
- `UpdateTableSchemaInputDto`: Request to update schema
- `CreateTableColumnDto`: Column definition

**Output DTOs**:
- `CreateTableOutputDto`: Creation result
- `UpdateTableSchemaOutputDto`: Schema update result
- `GetTableInfoOutputDto`: Table information

DTOs are Pydantic models for automatic validation.

### 3. Infrastructure Layer (Adapters)

**Location**: `infrastructure/`

Implements interfaces defined in domain layer using external services.

#### AWS Glue Repository (`infrastructure/repositories.py`)

Implements `IcebergTableRepository` using boto3:

```python
class AwsGlueIcebergTableRepository(IcebergTableRepository):
    async def save(table: IcebergTable) -> None:
        # Create table in AWS Glue with ICEBERG format
    
    async def update(table: IcebergTable) -> None:
        # Update table schema in AWS Glue
    
    async def exists(table_name: TableName) -> bool:
        # Check if table exists in Glue
```

**Responsibilities**:
- Translate domain entities to AWS Glue format
- Handle AWS API calls
- Manage database creation
- Generate S3 locations
- Convert errors to domain exceptions

### 4. Presentation Layer (HTTP API)

**Location**: `presentation/`

Handles HTTP requests and responses.

#### Routes (`presentation/routes.py`)

```python
POST /api/v1/tables
  ├─ Parse CreateTableInputDto
  ├─ Call CreateTableUseCase
  ├─ Transform output to JSON
  └─ Handle exceptions

POST /api/v1/tables/{table_name}/schema
  ├─ Parse UpdateTableSchemaInputDto
  ├─ Call UpdateTableSchemaUseCase
  └─ Return schema evolution results

GET /api/v1/tables/{table_name}
  ├─ Call GetTableInfoUseCase
  └─ Return table information
```

**Responsibilities**:
- HTTP request/response handling
- Input validation (Pydantic)
- Error to HTTP status code mapping
- Response formatting

## Data Flow Example: Create Table

```
1. HTTP Request
   POST /api/v1/tables
   {
     "contract_id": "users_v1",
     "name": "users",
     "columns": [...]
   }
   ↓

2. Presentation Layer (routes.py)
   ├─ Parse CreateTableInputDto
   ├─ Log request
   └─ Call create_table_use_case.execute()
   ↓

3. Application Layer (use_cases.py)
   ├─ Validate input
   ├─ Build domain entities
   ├─ Call table.validate()
   ├─ Call repository.create_database_if_not_exists()
   ├─ Call repository.exists()
   └─ Call repository.save()
   ↓

4. Domain Layer (entities.py)
   ├─ IcebergTable.validate()
   │  └─ Check columns not empty
   │  └─ Check no duplicates
   └─ Table business rules enforced
   ↓

5. Infrastructure Layer (repositories.py)
   ├─ Build Glue table format
   ├─ Call boto3 glue.create_table()
   ├─ Handle AlreadyExistsException
   └─ Wrap errors in domain exceptions
   ↓

6. AWS Glue
   └─ Table created
   ↓

7. Response
   HTTP 201 Created
   {
     "data": {
       "status": "created",
       "table_name": "users",
       ...
     }
   }
```

## Key DDD Principles Applied

### 1. Entity vs Value Object

**Entities** (have identity):
- `IcebergTable` - Has identity, mutable lifecycle
- `SchemaEvolution` - Tracks specific changes

**Value Objects** (no identity, immutable):
- `TableName` - No identity, immutable
- `Column` - Defined by attributes
- `Version` - Defined by semantic version

### 2. Aggregate Root

`IcebergTable` is the aggregate root:
- Entry point for accessing table data
- Enforces business rules
- Manages related entities (columns)
- Validates consistency

### 3. Repository Pattern

`IcebergTableRepository` abstracts persistence:
- Domain layer doesn't know about AWS Glue
- Can swap implementations (Glue ↔ Database)
- Testable with mock repositories

### 4. Use Cases

Each business operation is a dedicated use case:
- `CreateTableUseCase`
- `UpdateTableSchemaUseCase`
- `GetTableInfoUseCase`

Not a generic CRUD service.

### 5. Ubiquitous Language

Domain terms are consistently used:
- "Table" = IcebergTable entity
- "Schema Evolution" = SchemaEvolution value object
- "Status" = TableStatus value object
- Code mirrors business terminology

## Benefits of This Architecture

### 1. Separation of Concerns
- Domain logic isolated from infrastructure
- Easy to test business rules without AWS
- Infrastructure changes don't affect business logic

### 2. Maintainability
- Clear structure: Domain → Application → Infrastructure
- Each layer has single responsibility
- Easy to navigate and understand

### 3. Testability
```python
# Test domain logic without mocks
table = IcebergTable(...)
table.validate()  # Pure Python, no AWS needed

# Test use cases with mock repository
mock_repo = MockRepository()
use_case = CreateTableUseCase(mock_repo)
result = await use_case.execute(dto)

# Test API with test client
response = client.post("/api/v1/tables", json=payload)
```

### 4. Scalability
- Easy to add new use cases
- New data types follow pattern
- Consistent error handling
- Infrastructure can be upgraded independently

### 5. Business Clarity
- Domain entities embody business concepts
- Business rules are enforced in domain layer
- Easy to reason about what's possible

## File Structure

```
iceberg_creation_service/
├── domain/                    # Pure business logic
│   ├── __init__.py
│   ├── entities.py           # Domain entities
│   ├── value_objects.py      # Immutable value objects
│   ├── repositories.py       # Repository interface
│   └── exceptions.py         # Domain exceptions
│
├── application/              # Use cases
│   ├── __init__.py
│   ├── use_cases.py         # Business operations
│   └── dto.py               # Data transfer objects
│
├── infrastructure/           # External dependencies
│   ├── __init__.py
│   └── repositories.py      # AWS Glue implementation
│
├── presentation/            # HTTP API
│   ├── __init__.py
│   └── routes.py            # FastAPI endpoints
│
├── config.py                # Configuration
├── main.py                  # App factory with DI
└── __init__.py
```

## Testing Examples

### Domain Layer (No AWS needed)
```python
def test_table_validation():
    table = IcebergTable(
        table_name=TableName("users"),
        columns=[Column("id", DataType.STRING)],
        ...
    )
    table.validate()  # Pure Python

def test_schema_evolution():
    old_cols = [Column("id", DataType.STRING)]
    new_cols = [Column("id", DataType.STRING), Column("email", DataType.STRING)]
    evolution = table.update_schema(new_cols)
    assert len(evolution.added_columns) == 1
```

### Application Layer (Mock repository)
```python
class MockRepository(IcebergTableRepository):
    async def save(self, table): self.tables[str(table.table_name)] = table
    async def exists(self, name): return str(name) in self.tables
    ...

async def test_create_table():
    repo = MockRepository()
    use_case = CreateTableUseCase(repo)
    result = await use_case.execute(input_dto)
    assert result.status == "created"
```

### Infrastructure Layer (Test AWS integration)
```python
@pytest.mark.integration
async def test_glue_create_table(glue_client):
    repo = AwsGlueIcebergTableRepository()
    table = IcebergTable(...)
    await repo.save(table)
    # Verify in AWS Glue
```

## Migration Notes

If upgrading from the old codebase:

1. **Old imports**: `from iceberg_creation_service.adapters import...`
   → **New imports**: `from iceberg_creation_service.infrastructure.repositories import...`

2. **Old models**: `iceberg_creation_service.models`
   → **New DTOs**: `iceberg_creation_service.application.dto`

3. **Old routing**: `iceberg_creation_service.routers.tables`
   → **New routes**: `iceberg_creation_service.presentation.routes`

The API remains the same, only internal structure changed.

## Future Enhancements

DDD makes these easier to add:

1. **Event Sourcing**: Track all table changes as events
2. **CQRS**: Separate read/write models
3. **Specification Pattern**: Complex business rules
4. **Anti-Corruption Layer**: Integrate with other bounded contexts
5. **Multi-tenancy**: Add tenant context to domain
6. **Audit Trail**: Track who changed what and when

## References

- [Domain-Driven Design - Eric Evans](https://www.domainlanguage.com/ddd/)
- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Python DDD Patterns](https://pydantic-docs.helpmanual.io/)