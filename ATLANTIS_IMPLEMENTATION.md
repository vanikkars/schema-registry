# Atlantis Implementation for Schema Registry

## Overview

This implementation provides **automatic contract validation and PR merging** similar to [Atlantis](https://www.runatlantis.io/), but specifically for your schema registry system.

## What Was Created

### 1. GitHub Actions Workflow
**File:** `.github/workflows/atlantis-schema-validation.yml`

Automatically triggered when PRs modify contracts in the `contracts/` folder.

**Workflow:**
1. Detects changed contract files
2. Validates JSON structure
3. Sends contracts to registry API (`POST /api/v1/schemas`)
4. Posts validation results as PR comment
5. Auto-merges PR if all validations passed

**Key Features:**
- ✅ Automatic trigger on PR creation/update
- ✅ Validation report posted to PR
- ✅ Auto-merge on success (squash merge)
- ✅ Blocks merge on validation failure
- ✅ Handles API connection errors gracefully

### 2. Validation Script
**File:** `scripts/validate-contracts.py`

Standalone Python script for local or CI/CD validation.

**Capabilities:**
- Validates individual files, directories, or all contracts
- Sends contracts to registry API for approval
- Generates validation reports
- Can export results to JSON
- Works with local and remote APIs

**Usage:**
```bash
python scripts/validate-contracts.py                           # All contracts
python scripts/validate-contracts.py contracts/user/           # Specific dir
python scripts/validate-contracts.py contracts/user/02/file.json  # Single file
python scripts/validate-contracts.py --registry-url <URL>      # Remote API
python scripts/validate-contracts.py --export results.json     # Export results
```

### 3. Documentation

#### `ATLANTIS_QUICKSTART.md`
5-minute quick start guide covering:
- GitHub secrets setup
- How to create contract PRs
- Troubleshooting common issues
- Makefile commands

#### `docs/ATLANTIS_SETUP.md`
Comprehensive setup and configuration guide:
- Detailed workflow explanation
- Advanced configuration options
- CI/CD integration
- Monitoring and alerts
- Docker environment setup

### 4. Helper Scripts

#### `scripts/setup-atlantis.sh`
Installation and verification script that:
- Makes scripts executable
- Enables pre-commit hooks
- Verifies workflow files exist
- Provides next steps

#### `.git/hooks/pre-commit`
Git pre-commit hook that:
- Validates contract JSON before commit
- Prevents bad JSON from entering repository
- Optional (can be skipped with `--no-verify`)

### 5. Makefile Commands
Added validation commands to Makefile:

```bash
make validate-contracts     # Validate all contracts
make validate-export        # Validate and export to JSON
make validate-remote        # Validate against remote API
```

### 6. Configuration Files

#### `scripts/requirements.txt`
Python dependencies for validation script:
```
requests>=2.31.0
```

## Architecture

### Workflow Flow

```
Pull Request Created with Contract Changes
         ↓
GitHub Actions Triggers
(atlantis-schema-validation.yml)
         ↓
For Each Changed Contract File:
  ├─ Parse JSON
  ├─ Validate Schema
  ├─ POST to /api/v1/schemas
  └─ Collect Result
         ↓
Post Comment on PR (Results Table)
         ↓
Check Overall Status:
  ├─ All Passed? → Auto-Merge ✅
  └─ Any Failed? → Block Merge ❌
```

### Component Interaction

```
┌─────────────────────────────────────────┐
│   GitHub Repository                      │
│  ┌───────────────────────────────────┐  │
│  │ Pull Request                       │  │
│  │ (contract changes)                 │  │
│  └───────────────┬─────────────────────┘  │
│                  │                        │
│  ┌──────────────┴────────────────────┐  │
│  │ GitHub Actions Workflow            │  │
│  │ atlantis-schema-validation.yml     │  │
│  └──────────────┬────────────────────┘  │
│                 │                        │
└─────────────────┼────────────────────────┘
                  │
                  ├─ Runs: validate-contracts.py
                  │
                  └─ Posts to: /api/v1/schemas
                               (Registry API)
                               (Docker Container)
                               (AWS Glue)
```

## Usage Workflow

### For Developers

1. **Create feature branch**
   ```bash
   git checkout -b add-order-contract
   ```

2. **Add/modify contracts**
   ```bash
   # Edit contracts/order/02/order_v1.json
   ```

3. **Test locally (optional)**
   ```bash
   make docker-up           # Start API
   make validate-contracts  # Validate in another terminal
   ```

4. **Push and create PR**
   ```bash
   git push origin add-order-contract
   # Open PR on GitHub
   ```

5. **Wait for automation**
   - Workflow runs (1-2 minutes)
   - Comment posted with results
   - Auto-merges if all pass ✅
   - Blocks if any fail ❌

### For Failed Validations

1. **Read error** in PR comment
2. **Fix contract** (missing fields, invalid JSON, etc.)
3. **Commit and push** - workflow runs again automatically
4. **Success** → PR auto-merges

## Configuration

### GitHub Secrets

Set these in repository Settings → Secrets and variables → Actions:

| Secret | Value | Required | Default |
|--------|-------|----------|---------|
| `REGISTRY_API_URL` | API endpoint | No | `http://localhost:8000` |

### Workflow Customization

Edit `.github/workflows/atlantis-schema-validation.yml`:

**Change merge method:**
```yaml
merge_method: 'squash'  # or 'merge', 'rebase'
```

**Modify commit message:**
```yaml
commit_title: "Your custom title"
commit_message: "Your custom message"
```

**Adjust timeouts:**
```yaml
timeout: 30  # seconds in validation script
```

## Contract Requirements

Every contract must have:

```json
{
  "name": "schema-name",
  "namespace": "com.example.namespace",
  "type": "record",
  "fields": [
    {
      "name": "field_name",
      "type": "string",
      "doc": "Field description"
    }
  ],
  "data_owner": "Team Name",
  "data_steward": "Team Name",
  "sla_uptime_percentage": 99.95,
  "sla_max_latency_ms": 5000
}
```

**Required fields:**
- `name` - Unique identifier
- `namespace` - AVRO namespace (dot-separated)
- `type` - Always "record"
- `fields` - Array with at least one field

## Testing

### Local Testing

```bash
# 1. Start API
cd /path/to/schema-registry
make docker-up

# 2. In another terminal, validate
python scripts/validate-contracts.py

# 3. Test against remote API
python scripts/validate-contracts.py --registry-url https://api.example.com
```

### Workflow Testing

Create a test PR with:
- A new contract file or
- A modified contract file

Monitor in GitHub → Actions tab.

## Troubleshooting

### Issue: Workflow doesn't run

**Solution:**
- Verify `.github/workflows/atlantis-schema-validation.yml` exists
- Push branch to GitHub (not just local)
- Check "Actions" tab for error messages

### Issue: "Cannot connect to registry API"

**Solution:**
- Ensure registry API is running: `make docker-up`
- Verify `REGISTRY_API_URL` secret is set correctly
- For local dev, expose API with: `ngrok http 8000`
- Check firewall/network rules for remote APIs

### Issue: Contract validation fails

**Solution:**
- Run locally: `python scripts/validate-contracts.py`
- Validate JSON: `python -m json.tool contracts/file.json`
- Check required fields are present
- Compare against existing valid contracts

### Issue: PR won't auto-merge

**Solution:**
- Enable auto-merge in repo Settings
- Check for merge conflicts
- Verify all status checks passed
- Review branch protection rules

## Files Summary

```
schema-registry/
├── .github/
│   └── workflows/
│       └── atlantis-schema-validation.yml      ← Main workflow
├── scripts/
│   ├── validate-contracts.py                   ← Validation script
│   ├── setup-atlantis.sh                       ← Setup script
│   └── requirements.txt                        ← Dependencies
├── .git/
│   └── hooks/
│       └── pre-commit                          ← Git pre-commit hook
├── docs/
│   └── ATLANTIS_SETUP.md                       ← Full documentation
├── ATLANTIS_QUICKSTART.md                      ← Quick start guide
├── ATLANTIS_IMPLEMENTATION.md                  ← This file
└── Makefile                                    ← Updated with validation commands
```

## Next Steps

1. **Install dependencies:**
   ```bash
   pip install -r scripts/requirements.txt
   ```

2. **Run setup script:**
   ```bash
   bash scripts/setup-atlantis.sh
   ```

3. **Test locally:**
   ```bash
   make docker-up
   make validate-contracts
   ```

4. **Commit and push:**
   ```bash
   git add .github/ scripts/ docs/ Makefile ATLANTIS_*.md
   git commit -m "Add Atlantis-like contract validation automation"
   git push origin refactoring-2
   ```

5. **Create PR on main branch**

6. **Test with real PR:**
   - Create test branch
   - Modify a contract
   - Open PR to main
   - Watch automation work!

## Benefits

✅ **Automated Validation** - No manual checking needed
✅ **Fast Feedback** - Results within 1-2 minutes
✅ **Guardrails** - Prevents bad contracts from merging
✅ **Self-Service** - Developers can fix and re-push
✅ **Audit Trail** - All validations recorded in PR
✅ **Scalable** - Works with any API endpoint
✅ **Reversible** - Can disable auto-merge anytime

## Support

- **Quick Start:** Read `ATLANTIS_QUICKSTART.md`
- **Full Docs:** Read `docs/ATLANTIS_SETUP.md`
- **Validation Script:** `python scripts/validate-contracts.py --help`
- **Workflow Logs:** GitHub → Actions → [workflow name]

## References

- [Atlantis Documentation](https://www.runatlantis.io/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [AWS Glue Schema Registry](https://docs.aws.amazon.com/glue/latest/dg/schema-registry-landing.html)
- [AVRO Specification](https://avro.apache.org/docs/current/spec.html)