# Schema Registry Contract Automation - Quick Start

This guide sets up **automatic contract validation and PR merging** using GitHub Actions and ngrok.

## 🎯 What This Does

```
Pull Request with Contract Changes
          ↓
GitHub Actions Workflow Triggers
          ↓
Validates Each Contract via Registry API
          ↓
If All Valid → Auto-Merge PR ✅
If Any Invalid → Block Merge + Comment with Errors ❌
```

## ⚡ 5-Minute Setup

### Step 1: Expose Local API with ngrok

Since GitHub Actions runs in the cloud and cannot reach `localhost:8000`, you need to expose your API:

```bash
# Terminal 1: Start your API
make docker-up

# Terminal 2: Expose with ngrok
ngrok http 8000

# Output will show:
# Forwarding    https://abc123def456.ngrok.io -> http://localhost:8000
```

**See [docs/NGROK_SETUP.md](docs/NGROK_SETUP.md) for detailed ngrok setup**

### Step 2: Create GitHub Secret

1. Copy the ngrok HTTPS URL (e.g., `https://abc123def456.ngrok.io`)
2. Go to your GitHub repository
3. **Settings** → **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add:

| Name | Value |
|------|-------|
| `REGISTRY_API_URL` | Paste your ngrok URL here |

Example:
```
Name: REGISTRY_API_URL
Value: https://abc123def456.ngrok.io
```

> **Note:** Free ngrok generates a new URL each time you restart. If it changes, just update the GitHub secret with the new URL.

### Step 3: Files Already Added

The workflow is ready to go! These files were added:

```
.github/workflows/
└── contract-validation-workflow.yml  ← Main workflow

scripts/
└── validate-contracts.py              ← Validation script

docs/
├── CONTRACT_AUTOMATION_SETUP.md       ← Full documentation
└── NGROK_SETUP.md                    ← ngrok guide

Makefile                               ← Added validation commands
```

### Step 4: Test Locally

Before pushing to GitHub:

```bash
# Start the registry API
make docker-up

# Test validation in another terminal
make validate-contracts

# Test specific directory
python scripts/validate-contracts.py contracts/user/

# Export results
make validate-export
```

## 🚀 How to Use

### Creating a Contract PR

1. **Create a new branch**
   ```bash
   git checkout -b add-new-contract
   ```

2. **Add or modify a contract**
   ```bash
   # Example: contracts/order/02/order_v1.json
   ```

3. **Test locally (optional but recommended)**
   ```bash
   python scripts/validate-contracts.py contracts/order/02/
   ```

4. **Commit and push**
   ```bash
   git add contracts/
   git commit -m "Add order contract v1"
   git push origin add-new-contract
   ```

5. **Open PR on GitHub**
   - The workflow automatically triggers
   - Wait 1-2 minutes for validation
   - If passed → PR auto-merges! 🎉
   - If failed → See comment with error details

### Fixing Failed Validations

If validation fails:

1. **Read the error** in the PR comment
2. **Fix the contract** (e.g., add missing fields)
3. **Commit and push** new changes
4. **Workflow runs again** automatically
5. **Once fixed** → Auto-merge happens

## 📋 Contract Requirements

Every contract must have these fields:

```json
{
  "name": "unique-contract-name",
  "namespace": "com.example.data",
  "type": "record",
  "fields": [
    {
      "name": "field_name",
      "type": "string",
      "doc": "Description"
    }
  ]
}
```

**Required fields:**
- `name` - Unique identifier
- `namespace` - AVRO namespace
- `type` - Always "record" for data contracts
- `fields` - Array of field definitions

## 🔧 Makefile Commands

```bash
# Validate all contracts
make validate-contracts

# Validate specific directory
python scripts/validate-contracts.py contracts/user/

# Validate and export to JSON
make validate-export

# Test against remote API
python scripts/validate-contracts.py --registry-url https://api.example.com
```

## 🐛 Troubleshooting

### Workflow doesn't run
- Check `.github/workflows/atlantis-schema-validation.yml` exists
- Verify branch is pushed to GitHub
- Check "Actions" tab in repository

### "Cannot connect to registry API"
- **Most common:** ngrok is not running
  ```bash
  # Terminal 1: Ensure API is running
  make docker-up
  
  # Terminal 2: Start ngrok
  ngrok http 8000
  ```
- Check `REGISTRY_API_URL` secret matches ngrok URL exactly
- Verify ngrok URL is HTTPS (not HTTP)
- If ngrok URL changed, update GitHub secret

**See [docs/NGROK_SETUP.md](docs/NGROK_SETUP.md#troubleshooting) for detailed help**

### Contract validation fails
- Run locally: `python scripts/validate-contracts.py`
- Check JSON is valid: `python -m json.tool contracts/file.json`
- Verify required fields are present
- Check against example in `/contracts` folder

### PR won't auto-merge
- Enable auto-merge in repo settings
- Check for merge conflicts
- Verify all status checks passed
- Check branch protection rules

### ngrok URL keeps changing
- Free ngrok generates new URL each restart
- Update GitHub secret when URL changes
- Or upgrade to ngrok Pro ($5/mo) for static URL
- See [docs/NGROK_SETUP.md](docs/NGROK_SETUP.md#option-1-ngrok-pro-static-url)

## 📚 Full Documentation

See [docs/CONTRACT_AUTOMATION_SETUP.md](docs/CONTRACT_AUTOMATION_SETUP.md) for:
- Advanced configuration
- CI/CD integration
- Monitoring & alerts
- Docker setup

## 🔗 Workflow Diagram

```
Contract PR Created
        ↓
GitHub Actions Workflow Starts (detect changes in contracts/)
        ↓
For Each Contract File:
  ├─ Load JSON
  ├─ Validate schema
  ├─ POST to /api/v1/schemas via ngrok
  └─ Check response (200/201 = pass)
        ↓
Post Comment on PR (results table)
        ↓
All Passed? 
  ├─ Yes → Auto-Merge ✅
  └─ No  → Block Merge ❌
```

## 🎯 Next Steps

1. **Test the workflow**: Create a test PR with a small contract change
2. **Configure remote API**: Update `REGISTRY_API_URL` secret when deploying
3. **Set merge preferences**: Choose squash/merge/rebase in repo settings
4. **Add branch protection**: Require validated contracts before merging

## 📖 References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Atlantis Documentation](https://www.runatlantis.io/)
- [AWS Glue Schema Registry](https://docs.aws.amazon.com/glue/latest/dg/schema-registry-landing.html)

## ❓ Questions?

- Check workflow logs: GitHub → Actions → [workflow name]
- Run script manually: `python scripts/validate-contracts.py`
- Read detailed docs: `docs/ATLANTIS_SETUP.md`