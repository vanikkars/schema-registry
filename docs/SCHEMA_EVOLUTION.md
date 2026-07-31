# Schema Evolution

When a data contract is updated in the Schema Registry, both the Glue Schema Registry AND the Iceberg table are updated automatically, preserving existing data.

## How It Works

1. **New Schema Registered** → Update Glue Schema Registry with new version
2. **Table Exists** → Detect schema changes
3. **Analyze Changes** → Classify as safe or risky
4. **Update Iceberg Table** → Modify table schema, report changes and warnings

## Safe Changes (Automatically Applied)

### ✅ Adding New Columns

New nullable columns are added to the table without affecting existing data:

```json
{
  "status": "updated",
  "schema_changes": [
    "Added column: zip_code (string)",
    "Added column: last_login_at (timestamp)"
  ],
  "schema_warnings": []
}
```

**Why safe:** Existing rows get NULL values for new columns automatically.

## Risky Changes (Warnings Only)

### ⚠️ Removing Columns

Columns are removed but existing data is lost:

```json
{
  "status": "updated",
  "schema_changes": [],
  "schema_warnings": [
    "Removed column: last_login_at (data will be lost)"
  ]
}
```

**Risk:** Data in removed columns cannot be recovered.

### ⚠️ Changing Column Types

Type changes may break existing data:

```json
{
  "status": "updated",
  "schema_changes": [],
  "schema_warnings": [
    "Modified column type: zip_code (string → bigint)"
  ]
}
```

**Risk:** Existing string data may not convert to integer.

## API Response

```json
{
  "data": {
    "schema": { /* schema details */ },
    "table": {
      "name": "users_v1",
      "database": "iceberg_tables",
      "status": "updated",
      "schema_changes": [
        "Added column: new_field (type)"
      ],
      "schema_warnings": [
        "Removed column: old_field (data will be lost)"
      ]
    }
  }
}
```

### Status Values

- `created` - New table was created
- `exists` - Table already existed, no changes needed
- `updated` - Table schema was updated

## Examples

### Example 1: Add Optional Field

```bash
# Initial: user_name, email, date_of_birth
# Updated: user_name, email, date_of_birth, zip_code (new)

curl -X POST "http://localhost:8000/api/v1/schemas" \
  -H "Content-Type: application/json" \
  -d @contracts/user_v2.json
```

Response:
```json
{
  "schema_changes": ["Added column: zip_code (string)"],
  "schema_warnings": []
}
```

**Existing data:** Unaffected. New rows have NULL for zip_code.

### Example 2: Remove Field

```bash
# Initial: user_name, email, date_of_birth, zip_code
# Updated: user_name, email, date_of_birth (removed zip_code)

curl -X POST "http://localhost:8000/api/v1/schemas" \
  -H "Content-Type: application/json" \
  -d @contracts/user_v3.json
```

Response:
```json
{
  "schema_changes": [],
  "schema_warnings": ["Removed column: zip_code (data will be lost)"]
}
```

**Existing data:** zip_code column is removed. Data loss occurs.

### Example 3: Change Type

```bash
# Initial: zip_code (string)
# Updated: zip_code (integer)

curl -X POST "http://localhost:8000/api/v1/schemas" \
  -H "Content-Type: application/json" \
  -d @contracts/user_v4.json
```

Response:
```json
{
  "schema_changes": [],
  "schema_warnings": ["Modified column type: zip_code (string → bigint)"]
}
```

**Existing data:** Risky. String values may not convert to integer.

## Best Practices

### ✅ Do

1. **Add new columns as nullable** - Backward compatible
2. **Review warnings carefully** - Understand data loss implications
3. **Test with production data** - Validate type conversions
4. **Document schema changes** - Include reasoning in commit messages
5. **Plan migrations** - For risky changes, prepare data migration strategy

### ❌ Don't

1. **Ignore warnings** - Understand the risks before proceeding
2. **Remove columns without backup** - Ensure data is exported first
3. **Change types without testing** - Validate conversions work
4. **Make breaking changes in production** - Use staging environment first
5. **Skip version control** - Track all schema changes

## Schema Evolution Rules

| Change | Safe | Status | Action |
|--------|------|--------|--------|
| Add nullable column | ✅ Yes | Applied | Change |
| Remove column | ⚠️ No | Applied | Warning |
| Change column type | ⚠️ No | Applied | Warning |
| Make nullable column required | ⚠️ No | Applied | Warning |
| Reorder columns | ✅ Yes | Applied | No warning |

## Data Preservation

**Current Implementation:**

- ✅ Adding columns: Data preserved
- ✅ Removing columns: Table updated (data loss)
- ✅ Changing types: Table updated (conversion may fail)

**Future Enhancements:**

- Automatic data export before risky changes
- Schema change approval workflow
- Data migration validation
- Rollback capability
- Schema diff API endpoint

## Architecture

```
POST /api/v1/schemas
    ↓
RegisterSchemaUseCase
    ├─→ Schema Registry: register_schema()
    ├─→ Table Catalog: create_table()
    └─→ If exists: update_table_schema()
            ├─→ Get current table
            ├─→ Compare schemas
            ├─→ Detect changes
            ├─→ Update Glue table
            └─→ Return changes + warnings
    ↓
Response with schema_changes + schema_warnings
```

## Monitoring

Track schema evolution:

```bash
# Check latest changes
curl "http://localhost:8000/api/v1/schemas/users-v1/versions/latest"

# Monitor warnings
# Set up alerts for schema_warnings != []

# Audit trail
# Enable CloudTrail for Glue API calls
```
