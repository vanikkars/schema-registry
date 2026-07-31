# 🚀 Atlantis-like Schema Registry Automation

Automatic contract validation and PR merging for your schema registry, similar to [Atlantis](https://www.runatlantis.io/).

## Quick Links

- **Getting Started:** [`ATLANTIS_QUICKSTART.md`](ATLANTIS_QUICKSTART.md) ← Start here!
- **ngrok Setup (Important!):** [`docs/NGROK_SETUP.md`](docs/NGROK_SETUP.md) ← How to expose local API
- **Implementation Details:** [`ATLANTIS_IMPLEMENTATION.md`](ATLANTIS_IMPLEMENTATION.md)
- **Full Documentation:** [`docs/ATLANTIS_SETUP.md`](docs/ATLANTIS_SETUP.md)
- **Architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## What It Does

```
Pull Request with Contract Changes
         ↓
GitHub Actions Workflow Triggers
         ↓
Validates Each Contract via Registry API
         ↓
If All Valid → Auto-Merge PR ✅
If Any Invalid → Block Merge + Comment ❌
```

## Key Features

✅ **Automatic Validation** - On every PR that changes contracts
✅ **API Integration** - Sends contracts to `/api/v1/schemas`
✅ **PR Comments** - Posts validation results
✅ **Auto-Merge** - On successful validation (optional)
✅ **Local Testing** - Validate before pushing
✅ **Pre-commit Hook** - Prevent bad JSON from entering repo
✅ **Export Results** - JSON output for analysis

## Files Created

```
.github/workflows/
└── atlantis-schema-validation.yml         ← Main GitHub Actions workflow

scripts/
├── validate-contracts.py                  ← Standalone validation script
├── setup-atlantis.sh                      ← Installation script
└── requirements.txt                       ← Python dependencies

docs/
├── ATLANTIS_SETUP.md                      ← Full documentation
├── NGROK_SETUP.md                         ← ngrok setup guide ⭐ Important!
└── ARCHITECTURE.md                        ← System design & diagrams

Root:
├── ATLANTIS_README.md                     ← This file (overview)
├── ATLANTIS_QUICKSTART.md                 ← 5-minute setup guide
└── ATLANTIS_IMPLEMENTATION.md             ← Technical overview

.git/
└── hooks/pre-commit                       ← Git validation hook

Makefile (updated)
├── make validate-contracts
├── make validate-export
└── make validate-remote
```

## Quick Start

### 1. Expose Local API with ngrok (Important!)

GitHub Actions cannot reach `localhost:8000`. Use ngrok to expose your API:

```bash
# Terminal 1: Start API
make docker-up

# Terminal 2: Expose with ngrok
ngrok http 8000

# Output:
# Forwarding    https://abc123def456.ngrok.io -> http://localhost:8000
```

**Full guide:** See [docs/NGROK_SETUP.md](docs/NGROK_SETUP.md)

### 2. Set GitHub Secret

Copy the ngrok URL and add it to GitHub:

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `REGISTRY_API_URL`
4. Value: Paste your ngrok URL (e.g., `https://abc123def456.ngrok.io`)
5. Click **Add secret**

### 3. Install Dependencies (one-time)
```bash
pip install requests
```

### 4. Create a PR
1. Create feature branch: `git checkout -b add-contract`
2. Add/modify contract in `contracts/` folder
3. Push and create PR on GitHub
4. Watch workflow automatically validate and merge!

## How It Works

1. **You push** contract changes to GitHub
2. **GitHub Actions** detects the PR
3. **Workflow runs** automatically (detects `contracts/` changes)
4. **Validation script** checks each contract:
   - Validates JSON structure
   - Sends to `/api/v1/schemas`
   - Checks response (200/201 = pass)
5. **Posts comment** with results table
6. **Auto-merges** if all passed (optional)
7. **Blocks merge** if any failed

## Configuration

### GitHub Secrets (Required for Local Development)
Set in repository settings:
- `REGISTRY_API_URL` → **ngrok URL** (e.g., `https://abc123def456.ngrok.io`)
  - Free ngrok generates new URL each restart; update secret when it changes
  - ngrok Pro ($5/mo) provides static URL
  - See [docs/NGROK_SETUP.md](docs/NGROK_SETUP.md) for details

### Enable Auto-Merge (Optional)
Repository → Settings → Pull requests → ✅ Allow auto-merge

## Makefile Commands

```bash
make validate-contracts      # Validate all contracts
make validate-export         # Validate and export to JSON
make validate-remote         # Validate against remote API (prompts for URL)
```

## Example

### Creating a Contract PR

```bash
# 1. Create branch
git checkout -b add-order-contract

# 2. Add contract
cat > contracts/order/01/order_v1.json << 'JSON'
{
  "name": "order-v1",
  "namespace": "com.example.data",
  "type": "record",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "customer_id", "type": "string"},
    {"name": "amount", "type": "double"}
  ]
}
JSON

# 3. Test locally (optional)
python scripts/validate-contracts.py contracts/order/

# 4. Push and create PR
git push origin add-order-contract
# Open PR on GitHub
```

The workflow automatically:
1. Detects the new contract
2. Validates it
3. Posts validation results
4. Merges the PR if valid ✅

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Workflow doesn't run | Check `.github/workflows/` exists, push to GitHub, check Actions tab |
| Cannot connect to API | Ensure API running (`make docker-up`), check `REGISTRY_API_URL` secret |
| Contract validation fails | Run locally: `python scripts/validate-contracts.py`, check JSON syntax |
| PR won't auto-merge | Enable auto-merge in repo settings, check no conflicts/failed checks |

See [`ATLANTIS_QUICKSTART.md`](ATLANTIS_QUICKSTART.md#-troubleshooting) for more detailed troubleshooting.

## Documentation

- **Quick Start** (5 min) → [`ATLANTIS_QUICKSTART.md`](ATLANTIS_QUICKSTART.md)
- **ngrok Setup** (local API) → [`docs/NGROK_SETUP.md`](docs/NGROK_SETUP.md) ⭐ **Start here for local dev!**
- **Implementation** (technical) → [`ATLANTIS_IMPLEMENTATION.md`](ATLANTIS_IMPLEMENTATION.md)
- **Full Setup** (comprehensive) → [`docs/ATLANTIS_SETUP.md`](docs/ATLANTIS_SETUP.md)
- **Architecture** (system design) → [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Next Steps

- [ ] Read [`ATLANTIS_QUICKSTART.md`](ATLANTIS_QUICKSTART.md)
- [ ] Test locally: `make docker-up && python scripts/validate-contracts.py`
- [ ] Set GitHub secret `REGISTRY_API_URL` (if using remote API)
- [ ] Create a test PR with contract changes
- [ ] Enable auto-merge in repo settings (if desired)

## Architecture

```
GitHub PR
  ↓
GitHub Actions Workflow
  ↓
Validation Script (validate-contracts.py)
  ↓
Registry API (POST /api/v1/schemas)
  ↓
AWS Glue Schema Registry
```

For detailed architecture with diagrams, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Features Breakdown

### Automatic Validation ✅
- Detects contract changes in PRs
- Validates JSON syntax
- Checks required fields
- Sends to registry API

### API Integration ✅
- Sends contracts to `/api/v1/schemas`
- Checks response codes (200/201 = pass)
- Handles connection errors gracefully

### PR Comments ✅
- Posts validation results
- Shows pass/fail for each file
- Displays error details

### Auto-Merge ✅
- Merges PR if all validations pass
- Configurable merge method
- Respects branch protection rules

### Local Testing ✅
- Validate before pushing
- Test against remote APIs
- Export results to JSON

## Contract Requirements

Every contract must have:

```json
{
  "name": "schema-name",
  "namespace": "com.example",
  "type": "record",
  "fields": [
    {"name": "field", "type": "string"}
  ]
}
```

**Required fields:**
- `name` - Unique identifier
- `namespace` - AVRO namespace
- `type` - Always "record"
- `fields` - Array of fields

## References

- [Atlantis Documentation](https://www.runatlantis.io/)
- [GitHub Actions Guide](https://docs.github.com/en/actions)
- [AWS Glue Schema Registry](https://docs.aws.amazon.com/glue/latest/dg/schema-registry-landing.html)
- [AVRO Specification](https://avro.apache.org/docs/current/spec.html)

---

**Start with:** [`ATLANTIS_QUICKSTART.md`](ATLANTIS_QUICKSTART.md)

**Questions?** Check the documentation or run: `python scripts/validate-contracts.py --help`
