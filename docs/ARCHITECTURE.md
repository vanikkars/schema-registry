# Atlantis Schema Registry - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Repository                           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Pull Request                                             │   │
│  │  (Contract Changes in contracts/ folder)                  │   │
│  │                                                           │   │
│  │  Files changed:                                           │   │
│  │  - contracts/user/02/user_v1.json                        │   │
│  │  - contracts/order/01/order_v1.json                      │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │  GitHub Actions                                           │   │
│  │  Workflow Triggered (atlantis-schema-validation.yml)     │   │
│  │                                                           │   │
│  │  Steps:                                                   │   │
│  │  1. Detect changed contract files                        │   │
│  │  2. For each file:                                       │   │
│  │     - Load JSON                                          │   │
│  │     - Validate schema                                    │   │
│  │     - POST to /api/v1/schemas                            │   │
│  │     - Collect response                                   │   │
│  │  3. Aggregate results                                    │   │
│  │  4. Post comment to PR                                   │   │
│  │  5. Auto-merge if all pass                               │   │
│  └────────┬────────────────────────────────────────────────┘   │
│           │                                                      │
└───────────┼──────────────────────────────────────────────────────┘
            │
            │ API Calls (POST /api/v1/schemas)
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│               Registry API (FastAPI)                             │
│               (registry_api/main.py)                             │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  HTTP Router                                              │   │
│  │  (registry_api/adapters/inbound/http/router.py)         │   │
│  │                                                           │   │
│  │  Endpoint: POST /api/v1/schemas                          │   │
│  │  - Receives JSON contract                                │   │
│  │  - Returns 200/201 on success                            │   │
│  │  - Returns 400/500 on error                              │   │
│  └────────────────┬──────────────────────────────────────────┘   │
│                   │                                              │
│  ┌────────────────▼──────────────────────────────────────────┐   │
│  │  Use Cases / Application Logic                            │   │
│  │  (registry_api/application/use_cases.py)                │   │
│  │                                                           │   │
│  │  - Validate contract structure                           │   │
│  │  - Check compatibility                                   │   │
│  │  - Prepare for storage                                   │   │
│  └────────────────┬──────────────────────────────────────────┘   │
│                   │                                              │
│  ┌────────────────▼──────────────────────────────────────────┐   │
│  │  AWS Glue Adapter                                         │   │
│  │  (registry_api/adapters/outbound/aws_glue/)             │   │
│  │                                                           │   │
│  │  - Creates registry and schemas in AWS Glue             │   │
│  │  - Manages schema versions                               │   │
│  │  - Handles table catalog                                 │   │
│  └────────────────┬──────────────────────────────────────────┘   │
│                   │                                              │
└───────────────────┼──────────────────────────────────────────────┘
                    │
                    │ boto3 calls
                    │
                    ▼
        ┌─────────────────────────┐
        │  AWS Glue               │
        │  Schema Registry        │
        │  (AWS Account)          │
        └─────────────────────────┘
```

## Workflow Sequence Diagram

```
Developer              GitHub             Actions            Registry API
    │                    │                  │                    │
    │  Create PR          │                  │                    │
    ├─────────────────────>                  │                    │
    │                    │                   │                    │
    │                    │  Trigger Event    │                    │
    │                    ├──────────────────>│                    │
    │                    │                   │                    │
    │                    │                   │  Parse Files       │
    │                    │                   │  Validate JSON     │
    │                    │                   │                    │
    │                    │                   │  For Each File:    │
    │                    │                   │                    │
    │                    │                   │  POST Contract     │
    │                    │                   ├───────────────────>│
    │                    │                   │                    │
    │                    │                   │  ← Response (200)  │
    │                    │                   │<───────────────────┤
    │                    │                   │                    │
    │                    │                   │  Collect Results   │
    │                    │                   │                    │
    │                    │  Post Comment     │                    │
    │                    │<──────────────────┤                    │
    │                    │                   │                    │
    │  Read Results      │                   │                    │
    │<────────────────────                   │                    │
    │                    │                   │                    │
    │  All Valid?        │                   │                    │
    │  ├─ YES            │                   │                    │
    │  │  ├─ Auto-Merge  │                   │                    │
    │  │  │  Approve     │                   │                    │
    │  └─ NO             │                   │                    │
    │     └─ Fix & Push  │                   │                    │
    │                    │                   │                    │
    └────────────────────────────────────────────────────────────
```

## Component Architecture

### 1. GitHub Actions (Orchestrator)

```
atlantis-schema-validation.yml
├── Trigger: PR with contracts/* changes
├── Steps:
│   ├── Checkout code
│   ├── Setup Python
│   ├── Install dependencies
│   ├── Detect changed files
│   ├── Run validation script
│   ├── Post PR comment
│   └── Auto-merge if successful
└── Outputs:
    ├── PR comment with results
    ├── PR auto-merge (optional)
    └── Workflow status
```

### 2. Validation Script (Validator)

```
scripts/validate-contracts.py
├── Input:
│   ├── File path(s)
│   └── Registry API URL
├── Process:
│   ├── Load JSON files
│   ├── Validate schema
│   ├── Check required fields
│   ├── Send to API
│   └── Collect responses
├── Output:
│   ├── Results table (console)
│   ├── JSON export (optional)
│   └── Exit code (0 = success)
└── Error Handling:
    ├── JSON parse errors
    ├── Missing fields
    ├── API connection errors
    └── API validation errors
```

### 3. Registry API (Approver)

```
/api/v1/schemas (POST)
├── Input:
│   └── Contract JSON
├── Processing:
│   ├── Validate with Pydantic
│   ├── Check AVRO schema
│   ├── Verify compatibility
│   └── Store in AWS Glue
├── Output:
│   ├── 201: Created successfully
│   ├── 200: Updated successfully
│   ├── 400: Invalid contract
│   └── 500: Server error
└── Side Effects:
    ├── Creates/updates schemas
    ├── Manages versions
    └── Updates table catalog
```

## Data Flow

### Contract → GitHub → Validation → Merge

```
1. LOCAL DEVELOPMENT
   Developer creates/modifies:
   contracts/user/02/user_v1.json
   
   ├─ Required fields present ✓
   ├─ Valid JSON syntax ✓
   └─ Follows AVRO spec ✓

2. GITHUB PR
   Push to branch + Open PR
   
   ├─ Changed files detected
   ├─ Workflow triggered
   └─ Pipeline starts

3. VALIDATION (GitHub Actions)
   For each contract file:
   
   ├─ Load JSON
   ├─ Parse to Python dict
   ├─ Validate schema (pydantic)
   ├─ POST to /api/v1/schemas
   └─ Check response code
   
   Results:
   ├─ ✓ Pass → Store success
   ├─ ✗ Fail → Store error reason
   └─ Aggregate all results

4. REPORTING
   Post to PR:
   
   ├─ Comment with table
   ├─ List passed contracts
   ├─ List failed contracts
   ├─ Show error messages
   └─ Indicate auto-merge status

5. MERGE DECISION
   
   If all_passed == true:
   ├─ Call GitHub API
   ├─ Merge PR (squash)
   ├─ Close PR
   └─ Branch deleted
   
   If any_failed == true:
   ├─ Block merge
   ├─ Developer notified
   ├─ Developer fixes
   └─ Workflow runs again

6. AWS GLUE (Storage)
   Successful contracts stored:
   
   ├─ Schema Registry
   ├─ Version tracking
   ├─ Metadata
   └─ Change history
```

## Error Handling Flow

```
Contract File
    │
    ├─ JSON Parse Error
    │   └─ Report: Invalid JSON syntax
    │
    ├─ Missing Required Field
    │   └─ Report: Missing name/type/fields/namespace
    │
    ├─ API Connection Error
    │   └─ Report: Cannot reach registry API
    │
    ├─ API Response 400
    │   └─ Report: Contract validation failed
    │       (e.g., type mismatch, incompatibility)
    │
    ├─ API Response 500
    │   └─ Report: Server error, try again
    │
    └─ Success (200/201)
        └─ Report: Contract validated ✓
```

## Integration Points

### GitHub ↔ Workflow
- **Trigger:** PR events (opened, synchronize, reopened)
- **Input:** Repository code, changed files list
- **Output:** PR comments, auto-merge decision
- **Authentication:** GitHub token (automatic)

### Workflow ↔ Validation Script
- **Communication:** Command execution
- **Input:** File paths, API URL
- **Output:** Results JSON, exit code
- **Environment:** Python 3.11+

### Validation Script ↔ Registry API
- **Protocol:** HTTP POST
- **Endpoint:** `/api/v1/schemas`
- **Format:** JSON request/response
- **Authentication:** Optional (API dependent)
- **Timeout:** 30 seconds per request

### Registry API ↔ AWS Glue
- **Library:** boto3
- **Service:** AWS Glue Schema Registry
- **Operations:** CreateRegistry, CreateSchema, UpdateSchema
- **Authentication:** AWS credentials from environment

## Scalability Considerations

```
Single Contract PR
├─ 1-2 files → 1-2 requests → ~1-2 seconds

Multiple Contract PR
├─ 10-20 files → 10-20 requests → ~20-30 seconds

Parallel Processing (Future)
├─ Thread pool → Multiple concurrent API calls
├─ Batched requests → Group contracts
└─ Potential: 50% time reduction
```

## Security

```
Authentication:
├─ GitHub Actions → GitHub token (built-in)
├─ Validation Script → No auth required (local)
└─ Registry API → AWS credentials from environment

Authorization:
├─ PR author → Can push to branch
├─ GitHub Actions → Can comment and merge PRs
└─ Registry API → Validates against AWS permissions

Secrets Management:
├─ REGISTRY_API_URL → GitHub secret
├─ AWS credentials → Environment variables
└─ API responses → Logged but not sensitive
```

## Monitoring & Observability

```
GitHub Actions
├─ Run logs → Visible in Actions tab
├─ Step outputs → Detailed execution trace
├─ PR comments → User-facing results
└─ Workflow status → Badge in README (optional)

Validation Script
├─ Console output → Live progress
├─ Exit code → 0 (pass) or 1 (fail)
├─ JSON export → Machine-readable results
└─ File I/O → Audit trail of validations

Registry API
├─ Server logs → Docker container logs
├─ Response codes → Indicate success/failure
├─ Performance → Latency in responses
└─ Errors → Detailed error messages
```

## Deployment Topology

```
Development Environment:
└─ Local Docker: registry_api + PostgreSQL + Redis
   └─ Accessed by: validation script on localhost:8000

Staging Environment:
└─ Docker Compose or K8s: registry_api
   └─ Accessed by: GitHub Actions workflow via HTTP

Production Environment:
└─ Cloud deployment: Fargate/K8s/Lambda
   └─ Accessed by: GitHub Actions workflow via HTTPS
   └─ Secured by: TLS, API authentication
```

## Performance Characteristics

```
GitHub Actions:
├─ Startup time: 10-15 seconds
├─ Validation time: 1-2 seconds per contract
├─ Total time: ~20-30 seconds for typical PR
└─ Timeout: 6 hours (GitHub limit)

Validation Script:
├─ Load time: <100ms
├─ Parse JSON: <10ms per file
├─ API call: 200-500ms per request
└─ Total: Linear with number of files

Registry API:
├─ Request processing: 100-200ms
├─ AWS Glue calls: 500-1000ms
├─ Response time: 600-1200ms typical
└─ Depends on: AWS region, network latency
```

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS Glue Schema Registry](https://docs.aws.amazon.com/glue/latest/dg/schema-registry-landing.html)
- [AVRO Specification](https://avro.apache.org/docs/current/spec.html)