# Atlantis-like Schema Registry Automation

This document explains how to set up automatic schema validation and PR merging, similar to [Atlantis](https://www.runatlantis.io/).

## Overview

When you open a pull request that modifies contracts in the `contracts/` folder:

1. **GitHub Actions Workflow** runs automatically
2. **Contract Validation** - Each contract is sent to the registry API
3. **Approval Decision** - If all contracts are approved, the PR is auto-merged
4. **Comment Added** - A validation report is posted to the PR

## Setup

### 1. Expose Local API (if running locally)

GitHub Actions runs in the cloud and cannot reach `localhost:8000`. Use **ngrok** to expose your local API:

```bash
# Terminal 1: Start API
make docker-up

# Terminal 2: Expose with ngrok
ngrok http 8000

# Output: https://abc123def456.ngrok.io -> http://localhost:8000
```

**Full ngrok guide:** See [NGROK_SETUP.md](NGROK_SETUP.md)

### 2. GitHub Repository Secrets

Set up the registry API URL in your GitHub repository settings.

**Steps:**
1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `REGISTRY_API_URL`
5. Value: 
   - **Local dev:** ngrok URL (e.g., `https://abc123def456.ngrok.io`)
   - **Production:** Your deployed API URL (e.g., `https://api.example.com`)

If not set, the workflow defaults to `http://localhost:8000` (won't work for cloud-based workflows).

### 2. Enable Auto-Merge (Optional)

To enable automatic merging when all validations pass:

1. Repository → Settings → Pull requests
2. ✅ Enable "Allow auto-merge"
3. Choose merge method (we recommend "Squash and merge")

## How It Works

### Workflow Trigger

The workflow runs when:
- A PR is opened, updated, or reopened
- Files in `contracts/` folder are changed
- Workflow file itself is changed

### Validation Steps

For each changed contract file:

```
1. Extract JSON from file
2. Validate required fields (name, type, fields, namespace)
3. Send to /api/v1/schemas endpoint
4. Check API response
5. Report results
```

### Auto-Merge Conditions

PR is merged automatically when:
- ✅ All contract validations passed
- ✅ All GitHub checks passed
- ✅ PR has no conflicts
- ✅ PR is mergeable
- ✅ Repository allows auto-merge

### Failure Scenarios

If validation fails:
- ❌ PR is NOT merged
- 📝 Comment posted with failure reasons
- 🔧 Developer can fix and push new commits
- 🔄 Workflow runs again automatically

## Local Testing

### Test All Contracts

```bash
python scripts/validate-contracts.py
```

### Test Specific Directory

```bash
python scripts/validate-contracts.py contracts/user/
```

### Test Single Contract

```bash
python scripts/validate-contracts.py contracts/user/02/user_v1.json
```

### Test Against Remote API

```bash
python scripts/validate-contracts.py --registry-url https://api.example.com
```

### Export Results

```bash
python scripts/validate-contracts.py --export results.json
```

## Example Contract File

A valid contract must include:

```json
{
  "name": "users-v1",
  "namespace": "com.example.data",
  "type": "record",
  "doc": "User data contract",
  "fields": [
    {
      "name": "user_id",
      "type": "string",
      "doc": "Unique user identifier"
    },
    {
      "name": "email",
      "type": "string",
      "doc": "User email address"
    }
  ],
  "data_owner": "User Management Team",
  "data_steward": "Data Engineering",
  "sla_uptime_percentage": 99.95,
  "sla_max_latency_ms": 5000
}
```

## Troubleshooting

### Workflow Not Running

1. Check that workflow file exists: `.github/workflows/atlantis-schema-validation.yml`
2. Verify branch is pushed to GitHub
3. Check "Actions" tab to see workflow status

### Connection to API Failed

**Error:** "Cannot connect to registry API"

**Solutions:**
- Ensure `REGISTRY_API_URL` secret is set correctly
- Check that API is running and accessible
- For localhost during testing: use ngrok or similar to expose local API
- Check firewall rules if using remote API

### Contract Validation Fails

**Error:** "Invalid JSON" or "Missing required fields"

**Solutions:**
- Validate JSON syntax: `python -m json.tool contracts/file.json`
- Ensure all required fields are present
- Check field types match AVRO schema spec
- Run local validation: `python scripts/validate-contracts.py`

### PR Won't Auto-Merge

**Possible reasons:**
- Auto-merge not enabled in repository settings
- PR has merge conflicts
- Branch protection rules require additional reviews
- Required status checks haven't passed yet

### See Full Logs

1. Go to GitHub → Actions tab
2. Click the workflow run
3. Expand job to see detailed logs

## Advanced Configuration

### Customize Merge Method

Edit `.github/workflows/atlantis-schema-validation.yml`:

```yaml
merge_method: 'squash'  # Options: squash, merge, rebase
```

### Add Additional Validation

Modify the validation script in the workflow:

```yaml
- name: Validate contracts against registry API
  run: |
    # Add custom validation logic here
```

### Require Specific Approvers

Add branch protection rule in repository settings:
- Require pull request reviews before merging
- Dismiss stale pull request approvals
- Require status checks to pass

## Monitoring & Alerts

### Check Validation History

```bash
# View all workflow runs
gh run list --workflow atlantis-schema-validation.yml

# View specific run
gh run view <run-id> --log
```

### Set Up Notifications

GitHub automatically notifies about:
- Failed workflows in your PR
- Successful auto-merges
- Blocked merges due to validation

## CI/CD Integration

### Use in Other Workflows

Import the validation script in other workflows:

```yaml
- name: Validate contracts
  run: |
    python scripts/validate-contracts.py --export validation.json
```

### Docker Environment

Build validation into container:

```dockerfile
COPY scripts/validate-contracts.py /app/
RUN chmod +x /app/validate-contracts.py
```

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Atlantis Documentation](https://www.runatlantis.io/)
- [AWS Glue Schema Registry](https://docs.aws.amazon.com/glue/latest/dg/schema-registry-landing.html)
- [AVRO Schema Specification](https://avro.apache.org/docs/current/spec.html)