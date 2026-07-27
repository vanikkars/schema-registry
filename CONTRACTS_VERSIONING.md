# Data Contracts Versioning Guide

## Overview

Data contracts are now organized in a **versioned structure** demonstrating different schema evolution patterns supported by AWS Glue Schema Registry.

## Directory Structure

```
contracts/
├── test_contract.json                # Standalone test fixture (legacy, unchanged)
├── user/                             # User domain contracts
│   ├── user_v1.json                 # v1.0.0 - Original (3 columns)
│   └── user_v2.json                 # v2.0.0 - Evolved (BACKWARD compatible)
└── transaction/                      # Transaction domain contracts
    ├── transaction_v1.json          # v1.0.0 - Original (10 columns)
    └── transaction_v2.json          # v2.0.0 - Evolved (FORWARD compatible)
```

## Contract Patterns

### Pattern 1: BACKWARD Compatible Evolution (Users)

**Scenario**: Adding new optional fields without breaking existing systems.

**v1 → v2 changes**:
- ✅ Preserved: `user_name`, `email`, `date_of_birth` (required, unchanged)
- ✅ Added: `full_name`, `phone_number`, `last_login_at` (all nullable)

**Compatibility**:
- ✅ v1 readers can process v2 data (unknown fields are ignored)
- ✅ v1 writers work with v2 readers (nullable fields default to NULL)
- ✅ Glue mode: `BACKWARD`

**Real-world use case**: Gradual feature rollout where new fields are populated incrementally.

### Pattern 2: FORWARD Compatible Evolution (Transactions)

**Scenario**: Removing a field (e.g., for compliance) while supporting old readers.

**v1 → v2 changes**:
- ❌ Removed: `card_last_four` (PCI compliance concern)
- ✅ Added: `merchant_category_code`, `fraud_score` (nullable)

**Compatibility**:
- ⚠️ v1 readers receive v2 data but won't find `card_last_four` (NULL)
- ✅ v2 writers won't send the removed field
- ✅ Glue mode: `FORWARD`

**Real-world use case**: Security/compliance removals where old systems can gracefully handle missing data.

---

## Schema Registry Integration

### Registering a Contract

Both versions use the same `contract_id` (e.g., "users-v1") so Glue recognizes them as versions of a single schema:

```bash
# Register v2 (will be version 2 in Glue if v1 already registered)
curl -X POST http://localhost:8000/api/v1/schemas \
  -H "Content-Type: application/json" \
  -d @contracts/user/user_v2.json
```

### Glue Behavior

1. Glue checks `contract_id` to find the schema family
2. Validates the new version against compatibility mode
3. Increments `LatestSchemaVersion`
4. Stores as version N of the schema

### Checking Versions

```bash
# List all schemas
curl http://localhost:8000/api/v1/schemas

# Get specific schema details (all versions)
curl http://localhost:8000/api/v1/schemas/users-v1

# Get version info
curl http://localhost:8000/api/v1/schemas/users-v1/versions

# Get specific version (latest only in this implementation)
curl http://localhost:8000/api/v1/schemas/users-v1/versions/2
```

---

## Semantic Versioning

Each contract uses semantic versioning in the `version` field:
- `1.0.0` - Initial release
- `2.0.0` - Major version bump (breaking changes in terms of contract semantics, but validated by Glue compatibility mode)

The version is informational for clients; Glue tracks versions separately.

---

## Compatibility Modes Explained

### BACKWARD Compatibility
- **Readers**: Can process data written in newer versions
- **Use case**: Adding optional fields
- **Example**: v1 consumers reading v2 data with extra fields → ignore extra, process core fields
- **Glue validates**: New schema can only add optional fields, cannot remove/change required fields

### FORWARD Compatibility
- **Writers**: Can send data that older readers understand
- **Use case**: Removing fields that old readers won't expect
- **Example**: v2 writers dropping `card_last_four`, v1 readers just don't see it
- **Glue validates**: New schema can remove optional fields, cannot remove required fields

### BOTH Compatibility
- **Both directions**: Readers and writers of different versions coexist
- **Most restrictive**: Essentially no breaking changes allowed
- **Use case**: Maximum stability requirements

### NONE Compatibility
- **No validation**: Any schema change allowed
- **Risky**: Can break consumers silently
- **Use case**: Experimental/testing only

---

## Best Practices

1. **Name your contracts clearly**: Use domain names (`user/`, `transaction/`) as directories
2. **Version incrementally**: Start with v1, increment to v2, v3, etc.
3. **Document changes**: Include what changed in the description field
4. **Choose the right mode**:
   - New optional fields? → BACKWARD
   - Removing fields? → FORWARD
   - Complex changes? → Migrate in steps or use NONE in dev
5. **Test compatibility**: Register both versions and verify readers work

---

## Testing Locally

```bash
# Terminal 1: Start the API
cd registry_api && source ../.venv/bin/activate
python -m uvicorn registry_api.app.main:app --reload

# Terminal 2: Register v1
curl -X POST http://localhost:8000/api/v1/schemas \
  -H "Content-Type: application/json" \
  -d @contracts/user/user_v1.json

# Check it was registered
curl http://localhost:8000/api/v1/schemas/users-v1

# Register v2 (will be version 2 if v1 is already registered)
curl -X POST http://localhost:8000/api/v1/schemas \
  -H "Content-Type: application/json" \
  -d @contracts/user/user_v2.json

# Verify both versions exist
curl http://localhost:8000/api/v1/schemas/users-v1/versions
```

Note: Requires AWS credentials and an existing Glue Schema Registry in AWS.
