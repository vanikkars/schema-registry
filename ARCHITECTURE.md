# Architecture: Hexagonal Pattern (Ports & Adapters)

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                               │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Service                                │  CLI Tool         │  │
│  │  @router.post("/schemas")                       │  python app.py    │  │
│  │  async def create_schema(                       │                   │  │
│  │    registry: SchemaRegistry                     │  registry =       │  │
│  │  )                                              │  GlueSchemaReg()  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┬─┘
                                                                          │
                              Depends on abstraction
                                                                          │
┌─────────────────────────────────────────────────────────────────────────▼┐
│                              PORT LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  class SchemaRegistry(ABC):                                      │   │
│  │      async def register_schema(...) -> str                       │   │
│  │      async def get_schema(...) -> Optional[Dict]                │   │
│  │      async def list_schemas(...) -> List[Dict]                  │   │
│  │      async def get_versions(...) -> Optional[Dict]              │   │
│  │      async def create_table(...) -> Dict                        │   │
│  │      async def delete_schema(...) -> bool                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────┬──────────────────────────────┬─────────────────────┬────────────────┘
     │                              │                     │
  Implements                    Implements            Implements
     │                              │                     │
┌────▼──────────────┐      ┌────────▼────────┐      ┌────▼──────────────┐
│  ADAPTER LAYER    │      │ ADAPTER LAYER   │      │ ADAPTER LAYER     │
│                   │      │                 │      │                   │
│  AWS Glue         │      │  Mock Registry  │      │ Kafka             │
│  ┌─────────────┐  │      │ ┌─────────────┐ │      │ (Future)          │
│  │glue_registry│  │      │ │mock_registry│ │      │ ┌─────────────┐   │
│  │   class     │  │      │ │   class     │ │      │ │kafka_registry   │
│  │ implements  │  │      │ │ implements  │ │      │ │ (coming soon)   │
│  │   port      │  │      │ │   port      │ │      │ └─────────────┘   │
│  └─────────────┘  │      │ └─────────────┘ │      │                   │
│                   │      │                 │      │                   │
│  boto3.client()   │      │  In-memory      │      │  confluent-kafka  │
│  glue operations  │      │  dict storage   │      │  API calls        │
│                   │      │  for testing    │      │                   │
└─────────────────┬─┘      └────────┬────────┘      └────────┬──────────┘
                  │                 │                        │
             AWS API            Python dict            Kafka API
                  │                 │                        │
┌─────────────────▼─────────────────▼────────────────────────▼──────────┐
│                    EXTERNAL SERVICES                                   │
│  ┌──────────────────┐  ┌─────────────────────┐  ┌──────────────────┐ │
│  │  AWS Glue        │  │  Local Memory       │  │  Kafka Broker    │ │
│  │  Schema Registry │  │  (no external dep)  │  │  (future)        │ │
│  └──────────────────┘  └─────────────────────┘  └──────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Dependency Flow

### Without Decoupling (BEFORE)

```
API ──────────┐
              │
CLI ──────────► contracts_management/
              │
           (tight
            coupling)

Problem: Hard to test, hard to extend
```

### With Decoupling (AFTER)

```
API ──────────┐
              │
              ► SchemaRegistry (Port/Interface)
              │
CLI ──────────┘
              │
         (Depends on
          abstraction)
              │
         ┌────┴────┐
         │          │
   GlueRegistry   MockRegistry
   (Production)   (Testing)
   
Benefit: Easy to test, easy to extend
```

---

## File Organization

```
schema-registry/
│
├── core/                          ← CORE LAYER
│   ├── __init__.py
│   └── models.py                  (DataContract, ColumnDefinition, ContractMetadata)
│                                  (Pure data, no dependencies)
│
├── ports/                         ← PORT LAYER
│   ├── __init__.py
│   └── schema_registry.py         (SchemaRegistry ABC)
│                                  (Defines contracts)
│
├── adapters/                      ← ADAPTER LAYER
│   ├── __init__.py
│   ├── aws/
│   │   ├── __init__.py
│   │   └── glue_registry.py       (GlueSchemaRegistry - prod implementation)
│   │
│   └── mock/
│       ├── __init__.py
│       └── mock_registry.py       (MockSchemaRegistry - test implementation)
│
├── registry_api/                  ← PRESENTATION LAYER
│   ├── dependencies.py            (Dependency injection factory)
│   ├── __init__.py
│   └── app/
│       ├── __init__.py
│       ├── api.py                 (FastAPI routes using injected registry)
│       └── main.py                (FastAPI app initialization)
│
├── tests/                         ← TEST LAYER
│   ├── __init__.py
│   ├── conftest.py                (pytest configuration)
│   ├── test_api_decoupled.py      (Unit tests with MockSchemaRegistry)
│   └── test_api_endpoints.py      (Integration tests)
│
├── contracts_management/          ← LEGACY (Backward compatible)
│   ├── __init__.py
│   ├── models.py                  (Re-exports from core)
│   ├── upload_to_glue.py          (Original AWS code)
│   └── generate_contract.py       (Original generator code)
│
├── app/                           ← ORIGINAL CLI
│   ├── __init__.py
│   └── models.py
│
├── REFACTORING_SUMMARY.md         ← What changed
├── MIGRATION_GUIDE.md             ← How to update
├── QUICK_REFERENCE.md             ← Quick lookup
├── ARCHITECTURE.md                ← This file
└── pytest.ini                     ← Test config
```

---

## Data Flow Examples

### Example 1: Creating a Schema (Happy Path)

```
API Request: POST /api/v1/schemas
    │
    ├─► create_schema(contract, registry)
    │
    ├─► registry.register_schema(contract)
    │
    ├─► Which implementation? (Depends on ENVIRONMENT)
    │
    ├─► if ENVIRONMENT == "test":
    │       MockSchemaRegistry.register_schema()
    │       ├─ Add to self.schemas dict
    │       ├─ Return mock ARN
    │       └─ No AWS calls ✅
    │
    └─► else:
        GlueSchemaRegistry.register_schema()
        ├─ Call boto3.client.create_schema()
        ├─ Parse AWS response
        └─ Return ARN
```

### Example 2: Testing Without AWS

```
Test: test_register_schema
    │
    ├─► Create MockSchemaRegistry
    │   registry = MockSchemaRegistry()
    │
    ├─► Call register_schema
    │   arn = await registry.register_schema(contract)
    │
    ├─► Check result
    │   assert arn is not None ✅
    │
    └─► No AWS calls, no credentials needed, fast execution ✨
```

### Example 3: Adding New Implementation (Kafka)

```
1. Create new adapter
   adapters/kafka/kafka_registry.py
   class KafkaSchemaRegistry(SchemaRegistry):
       async def register_schema(...):
           # Kafka-specific code

2. Update dependency factory
   def get_schema_registry():
       if os.getenv("REGISTRY_TYPE") == "kafka":
           return KafkaSchemaRegistry()

3. Use it
   REGISTRY_TYPE=kafka uvicorn registry_api.app.main:app
   
Result: API works with Kafka without changing a single line! ✨
```

---

## Layer Responsibilities

### Core Layer
- **What**: Pure domain models
- **Responsibility**: Define data structures
- **No dependencies**: No AWS, no FastAPI, no external libs
- **Files**: `core/models.py`

### Port Layer
- **What**: Abstract interfaces
- **Responsibility**: Define contracts
- **Methods**: Register, retrieve, list schemas
- **Files**: `ports/schema_registry.py`

### Adapter Layer
- **What**: Concrete implementations
- **Responsibility**: Implement ports
- **AWS Adapter**: Uses boto3, talks to Glue
- **Mock Adapter**: In-memory storage for testing
- **Files**: `adapters/aws/glue_registry.py`, `adapters/mock/mock_registry.py`

### Presentation Layer
- **What**: API and CLI endpoints
- **Responsibility**: Handle requests, orchestrate
- **Depends on**: Port interface (not concrete implementations)
- **Files**: `registry_api/app/api.py`, `app/cli.py`

### Test Layer
- **What**: Test code
- **Responsibility**: Verify behavior
- **Uses**: MockSchemaRegistry for isolated testing
- **Files**: `tests/test_api_decoupled.py`, `tests/test_api_endpoints.py`

---

## Dependency Injection Pattern

```python
# 1. Define what you need (Port)
class SchemaRegistry(ABC):
    @abstractmethod
    async def register_schema(...): pass

# 2. Implement for different contexts (Adapters)
class GlueSchemaRegistry(SchemaRegistry):
    async def register_schema(self, contract):
        # AWS Glue implementation
        
class MockSchemaRegistry(SchemaRegistry):
    async def register_schema(self, contract):
        # Mock implementation

# 3. Factory decides which to use (Dependencies)
def get_schema_registry() -> SchemaRegistry:
    if os.getenv("ENVIRONMENT") == "test":
        return MockSchemaRegistry()
    return GlueSchemaRegistry()

# 4. API receives it (Dependency Injection)
@router.post("/schemas")
async def create_schema(
    registry: SchemaRegistry = Depends(get_schema_registry)
):
    await registry.register_schema(contract)

# 5. Can override in tests
app.dependency_overrides[get_schema_registry] = 
    lambda: MockSchemaRegistry()
```

---

## Benefits of This Architecture

### ✅ Testability
- Mock implementations don't need AWS
- Fast test execution (no network calls)
- Deterministic behavior (in-memory storage)

### ✅ Extensibility
- Add new implementations without changing existing code
- Open/Closed principle: Open for extension, closed for modification
- Just create new adapter and update factory

### ✅ Maintainability
- Each layer has single responsibility
- Clear separation of concerns
- Easy to find where logic lives

### ✅ Reusability
- Same interface used everywhere
- Same registry works in API, CLI, tests
- Logic not duplicated

### ✅ Flexibility
- Swap implementations at runtime (via env vars)
- Override in tests (via dependency overrides)
- Support multiple backends simultaneously

### ✅ Clarity
- Clear what depends on what
- Clear what each layer does
- Clear how to add new features

---

## SOLID Principles Applied

### S - Single Responsibility
- Core: Only models
- Ports: Only interface definition
- Adapters: Only one backend implementation each
- API: Only orchestration

### O - Open/Closed
- Open for extension: Can add new adapters
- Closed for modification: Don't change existing code
- New Kafka adapter? Just add `adapters/kafka/`

### L - Liskov Substitution
- Any `SchemaRegistry` implementation can be used anywhere
- `GlueSchemaRegistry` or `MockSchemaRegistry` are interchangeable

### I - Interface Segregation
- `SchemaRegistry` interface is focused
- Not bloated with unrelated methods
- Does what registry needs, nothing more

### D - Dependency Inversion
- High-level modules depend on abstractions
- Low-level modules (adapters) implement abstractions
- Not the other way around

---

## Comparison: Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| Model location | `contracts_management/` | `core/models.py` |
| AWS implementation | `contracts_management/upload_to_glue.py` | `adapters/aws/glue_registry.py` |
| Testing | Mock boto3 (complex) | MockSchemaRegistry (simple) |
| Adding new backend | Modify shared code | Create new adapter |
| API coupling | Tight to AWS | Loose to interface |
| Test speed | Slow (AWS calls) | Fast (in-memory) |
| Test dependencies | boto3 mock setup | Just MockSchemaRegistry |
| Code clarity | Mixed concerns | Clear layers |
| Reusability | Limited | High |
| Extensibility | Risky | Safe |

---

## Key Takeaway

By implementing the hexagonal architecture pattern:
1. **Isolate infrastructure** (AWS) from business logic (models)
2. **Define interfaces** (ports) that services depend on
3. **Implement adapters** for different backends
4. **Inject dependencies** so services don't care about implementation

Result: **More testable, maintainable, and extensible code.**

---

**Pattern**: Hexagonal Architecture (Ports & Adapters)  
**Status**: ✅ Implemented  
**Backward Compatible**: ✅ Yes  
**Ready for Production**: ✅ Yes