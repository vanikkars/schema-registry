# Using ngrok to Expose Local Services for GitHub Actions

When running your services locally (Registry API on `localhost:8000` and Iceberg Service on `localhost:8001`), GitHub Actions running in the cloud cannot reach them. **ngrok** exposes your local services to the internet so GitHub Actions can validate contracts and create Iceberg tables.

## What is ngrok?

**ngrok** creates a secure tunnel from your local machine to the internet, allowing external services (like GitHub Actions) to reach your local API.

```
Your PC
├─ Registry API (localhost:8000)
└─ Iceberg Service (localhost:8001)
    ↑
    │ ngrok tunnels
    │
Internet
    ↑
    │
GitHub Actions
  ├─ Validate schemas (REGISTRY_API_URL)
  └─ Create Iceberg tables (ICEBERG_SERVICE_URL)
```

## Installation

### macOS
```bash
brew install ngrok
```

### Linux
```bash
# Download from https://ngrok.com/download
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip
unzip ngrok-v3-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin
```

### Windows
Download from [https://ngrok.com/download](https://ngrok.com/download) and add to PATH.

### Verify Installation
```bash
ngrok --version
# Output: ngrok version 3.x.x
```

## Quick Start (5 minutes)

### Step 1: Start Your Services
```bash
docker-compose up -d
# Registry API is running on http://localhost:8000
# Iceberg Service is running on http://localhost:8001
```

### Step 2: Expose Services with ngrok (new terminal)

**⚠️ IMPORTANT - Free ngrok Limitations:**
- ❌ Can only run ONE tunnel at a time (not multiple simultaneously)
- ❌ No custom subdomains
- ❌ URLs change every session

**For Free ngrok Plan:**

You have two options:

**Option A: Expose only Registry API (Recommended for local testing)**
```bash
# Terminal 2: Expose Registry API only
ngrok http 8000
# Note the URL: https://abc123def456.ngrok.io
# This is your REGISTRY_API_URL
```

Then skip Iceberg service testing in GitHub Actions, or:

**Option B: Use ngrok Pro ($5/month) or free alternative**

If you need both services exposed:
- Upgrade to ngrok Pro (supports multiple tunnels + static domains)
- Or use a free alternative like LocalTunnel, Expose, or Cloudflare Tunnel

**For ngrok Pro Plan:**
```bash
# Terminal 2a: Expose Registry API
ngrok http 8000 --domain=registry-api.ngrok.io

# Terminal 2b: Expose Iceberg Service (in another terminal)
ngrok http 8001 --domain=iceberg-api.ngrok.io
```

You'll see output like:
```
ngrok by @inconshreveable                          (Ctrl+C to quit)

Session Status                online
Account                       Free
Region                        us (California)
Forwarding                    https://abc123def456.ngrok.io -> http://localhost:8000
Forwarding                    http://abc123def456.ngrok.io -> http://localhost:8000

Web Interface                 http://127.0.0.1:4040
```

### Step 3: Copy the HTTPS URL

**Free ngrok Plan:**
```
https://abc123def456.ngrok.io
```

⚠️ **Important:** This URL changes every time you restart ngrok! You'll need to update the GitHub secret each time.

**Pro Plan:**
```
https://registry-api.ngrok.io  (static URL, no need to update)
```

### Step 4: Set GitHub Secrets

**For Free ngrok Plan (Registry API only):**

1. Go to GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Create secret:
   - Name: `REGISTRY_API_URL`
   - Value: `https://abc123def456.ngrok.io` (from your ngrok)
   - Click **Add secret**

4. Leave `ICEBERG_SERVICE_URL` unset or set to your local URL (won't be reached from GitHub)

**⚠️ Free ngrok users:** Update the `REGISTRY_API_URL` secret each time ngrok restarts!

**For Pro Plan (Both Services):**

1. Set `REGISTRY_API_URL` → `https://registry-api.ngrok.io`
2. Set `ICEBERG_SERVICE_URL` → `https://iceberg-api.ngrok.io`
3. URLs are static, no need to update

### Step 5: Create a Test PR
Push a contract change and create a PR. GitHub Actions will now:
1. ✅ Reach your local Registry API (validate schemas)
2. ✅ Reach your local Iceberg Service (create tables)
3. ✅ Post results to PR

## How to Use ngrok

### Basic Usage
```bash
# Expose port 8000
ngrok http 8000

# Expose different port
ngrok http 3000

# Expose with custom domain (requires authentication)
ngrok http -subdomain=my-api 8000
```

### Verify Connection
```bash
# Test in another terminal
curl https://abc123def456.ngrok.io/health
# Should return: {"status": "ok"} or similar
```

### Monitor Traffic
ngrok provides a web dashboard:
```
Open http://127.0.0.1:4040 in browser
```

Shows:
- All requests to your API
- Request/response details
- Headers and body

## GitHub Actions Workflows

### Schema Validation Workflow
Once you set the `REGISTRY_API_URL` secret, the workflow automatically uses it:

```yaml
env:
  REGISTRY_API_URL: ${{ secrets.REGISTRY_API_URL || 'http://localhost:8000' }}
```

The workflow:
1. Reads `REGISTRY_API_URL` from GitHub secret
2. Validates contracts against Registry API
3. Posts validation results to PR
4. Auto-merges if all pass

### Iceberg Table Creation Workflow
Once you set the `ICEBERG_SERVICE_URL` secret, the workflow automatically uses it:

```yaml
env:
  ICEBERG_SERVICE_URL: ${{ secrets.ICEBERG_SERVICE_URL || 'http://localhost:8001' }}
```

The workflow:
1. Triggered after schema validation succeeds
2. Reads `ICEBERG_SERVICE_URL` from GitHub secret
3. Creates Iceberg tables for each contract
4. Posts creation results to PR

### Testing the Connection
The workflow logs will show:

**Schema Validation:**
```
📤 Sending contract to registry...
📍 Registry API: https://abc123def456.ngrok.io
✅ Contract validated
```

**Iceberg Table Creation:**
```
📤 Calling Iceberg service...
📍 Iceberg Service: https://iceberg-api.ngrok.io
✅ Table created: user_v1
```

## Important Considerations

### 1. ngrok Limitations (Free Version Only)

**Free ngrok limitations:**
- ❌ **Only ONE tunnel at a time** (can't run multiple ngrok instances)
- ❌ URLs change every time you restart
- ❌ Need to update GitHub secrets each time
- ❌ No custom subdomains

```bash
# Session 1:
ngrok http 8000
# URL: https://abc123def456.ngrok.io
# ✅ Works

# Try to start another tunnel:
ngrok http 8001
# ❌ ERROR: endpoint already online
# Can't run both simultaneously on free plan
```

**Solution:** 
- Upgrade to ngrok Pro ($5/month) for multiple tunnels + static URLs
- Or use LocalTunnel/Expose (free alternatives support multiple tunnels)
- Or test locally without routing through ngrok

### 2. Keep ngrok Running
ngrok must stay running while you test:

```bash
# Terminal 1: Start services
docker-compose up -d

# Terminal 2: Start ngrok for Registry API (keep running)
ngrok http 8000
# Copy URL: https://abc123def456.ngrok.io

# Terminal 3: Create PR and watch workflow
# GitHub Actions uses ngrok URL to reach Registry API
```

**Note:** Free ngrok only allows ONE tunnel, so you can only expose the Registry API. The Iceberg service workflow will only work if:
- You're using ngrok Pro
- Or you manually test locally without GitHub Actions

### 3. Update Secrets When URLs Change (Free ngrok)

**Important for free ngrok users:** When you restart ngrok, the URL changes. You must update the GitHub secret:

1. Get new URL from ngrok terminal
2. Go to GitHub → Settings → Secrets and variables → Actions
3. Update the secret:
   - `REGISTRY_API_URL` → new URL
4. Create another test PR

**Workaround:** 
- Use ngrok Pro for $5/month (supports multiple tunnels)
- Or use LocalTunnel/Expose (free alternatives)
- Or test locally without GitHub Actions

## Advanced Setup

### Option 1: ngrok Pro (Static URL)

For $5/month, ngrok Pro gives you a static domain:

```bash
# 1. Create ngrok account: https://dashboard.ngrok.com
# 2. Authenticate your local ngrok
ngrok config add-authtoken YOUR_TOKEN_HERE

# 3. Reserve a static domain in dashboard

# 4. Use it
ngrok http --domain=myapi.ngrok.io 8000

# URL never changes: https://myapi.ngrok.io
```

Then set GitHub secret once:
```
REGISTRY_API_URL = https://myapi.ngrok.io
```

### Option 2: Background Service

Keep ngrok running in background:

```bash
# macOS/Linux
ngrok http 8000 &

# Windows (PowerShell)
Start-Process ngrok -ArgumentList "http 8000" -WindowStyle Hidden
```

### Option 3: ngrok Configuration File

Create `~/.ngrok2/ngrok.yml`:

```yaml
authtoken: YOUR_AUTH_TOKEN
region: us
tunnels:
  api:
    proto: http
    addr: 8000
    subdomain: my-schema-api  # Requires Pro
    bind_tls: true
```

Then use:
```bash
ngrok start api
```

### Option 4: Docker Compose Integration (ngrok Pro only)

**Note:** This example requires ngrok Pro for static domains. Free ngrok doesn't support the `--domain` flag.

For **ngrok Pro**, add ngrok services to your docker-compose.yml:

```yaml
services:
  registry_api:
    ports:
      - "8000:8000"

  iceberg-creation:
    ports:
      - "8001:8001"

  ngrok-registry:
    image: ngrok/ngrok:latest
    environment:
      - NGROK_AUTHTOKEN=${NGROK_TOKEN}
    command: http registry_api:8000 --domain=registry-api.ngrok.io
    ports:
      - "4040:4040"

  ngrok-iceberg:
    image: ngrok/ngrok:latest
    environment:
      - NGROK_AUTHTOKEN=${NGROK_TOKEN}
    command: http iceberg-creation:8001 --domain=iceberg-api.ngrok.io
    ports:
      - "4041:4041"
```

Then:
```bash
export NGROK_TOKEN=your_token
docker-compose up
# ngrok automatically starts both services (Pro only)
# Registry API: https://registry-api.ngrok.io
# Iceberg Service: https://iceberg-api.ngrok.io
```

**For free ngrok users:** Use separate terminal commands instead (see Quick Start)

## Troubleshooting

### "Cannot connect to ngrok"

**Problem:** GitHub Actions can't reach ngrok URL

**Solutions:**
1. Verify ngrok is running: Check terminal with `ngrok http 8000`
2. Verify URL is correct: Check GitHub secret matches ngrok output
3. Check firewall: Ensure port 8000 is not blocked
4. Check API is running: `make docker-up` in another terminal

### "ngrok URL keeps changing"

**Problem:** Free ngrok generates new URL each session

**Solutions:**
1. Use ngrok Pro ($5/mo) for static URL
2. Update GitHub secret each time URL changes
3. Keep ngrok process always running
4. Deploy API to cloud for permanent solution

### "Connection refused"

**Problem:** ngrok can't reach localhost:8000

**Solutions:**
1. Verify API is running: `make docker-up`
2. Check port is correct: `curl http://localhost:8000/health`
3. Verify API port in docker-compose.yml
4. Check Docker daemon is running

### "Authentication failed"

**Problem:** ngrok says "authentication failed"

**Solutions:**
1. Create free account: https://ngrok.com
2. Get auth token from dashboard
3. Run: `ngrok config add-authtoken YOUR_TOKEN`
4. Restart ngrok

### "Workflow still can't reach services"

**Problem:** GitHub Actions shows "Cannot connect to registry API" or "Cannot connect to Iceberg service"

**Solutions:**
1. Check both secrets exist in GitHub:
   - `REGISTRY_API_URL`
   - `ICEBERG_SERVICE_URL`
2. Verify URL formats: `https://xxx.ngrok.io` (HTTPS, not HTTP)
3. Test URLs locally:
   ```bash
   curl https://abc123def456.ngrok.io/health         # Registry API
   curl https://iceberg-api.ngrok.io/health          # Iceberg Service
   ```
4. Check ngrok logs in web interfaces:
   - Registry: http://127.0.0.1:4040
   - Iceberg: http://127.0.0.1:4041 (if using separate ngrok)

## Monitoring

### Web Interface
```
Open http://127.0.0.1:4040
```

Shows:
- Real-time traffic
- Request/response details
- Headers, body, timing
- Errors and status codes

### Command Line
```bash
# See ngrok status
ps aux | grep ngrok

# Stop ngrok
pkill ngrok
```

### GitHub Actions Logs
```
GitHub → Actions → [workflow] → [run]
See all API requests and responses
```

## Complete Workflow Example (Free ngrok)

### Terminal Setup

**Free ngrok Note:** Can only expose Registry API (not both services simultaneously)

```bash
# Terminal 1: Start services
cd /path/to/schema-registry
docker-compose up -d

# Terminal 2: Expose Registry API with ngrok
ngrok http 8000
# Copy the URL: https://abc123def456.ngrok.io

# Terminal 3: Set GitHub secret (EVERY TIME URL CHANGES!)
# Go to GitHub → Settings → Secrets and variables → Actions
# Set: REGISTRY_API_URL = https://abc123def456.ngrok.io
# Leave ICEBERG_SERVICE_URL empty (can't run multiple ngrok tunnels)

# Terminal 4: Create test PR
git checkout -b test-contract
# Add a new contract file
git add contracts/current/example/example_v1.json
git commit -m "add example contract"
git push origin test-contract
# Open PR on GitHub
# Watch Actions tab!
# ✅ Schema validation workflow will run
# ❌ Iceberg table creation won't reach the service (no tunnel available)
```

### What Happens
1. ✅ Workflow triggers on PR creation
2. ✅ **Schema Validation Workflow**:
   - Reads `REGISTRY_API_URL` from GitHub secret
   - Uses ngrok to reach local Registry API
   - Validates contracts
   - Posts validation results to PR
   - Auto-merges if valid
3. ✅ **Iceberg Table Creation Workflow** (after merge):
   - Reads `ICEBERG_SERVICE_URL` from GitHub secret
   - Uses ngrok to reach local Iceberg Service
   - Creates Iceberg tables for each contract
   - Posts creation results to PR

## Production Deployment

When ready for production:

1. **Deploy both services** to cloud (AWS, Heroku, etc.)
2. **Update GitHub secrets** with production URLs
3. **Remove ngrok** locally
4. **Workflows continue to work** with production services

```bash
# Update secrets
REGISTRY_API_URL = https://prod-registry.your-domain.com
ICEBERG_SERVICE_URL = https://prod-iceberg.your-domain.com

# ngrok no longer needed
pkill ngrok
```

## Comparison: ngrok vs Other Options

| Option | Cost | Setup Time | URL Stability | Use Case |
|--------|------|------------|---------------|----------|
| ngrok Free | Free | 2 min | Changes each session | Local testing |
| ngrok Pro | $5/mo | 5 min | Permanent | Dev environment |
| Deployed API | Varies | 30+ min | Permanent | Production |
| LocalTunnel | Free | 2 min | Changes | Quick testing |
| Expose | Free | 2 min | Changes | Quick testing |

## References

- [ngrok Documentation](https://ngrok.com/docs)
- [ngrok GitHub](https://github.com/ngrok/ngrok)
- [ngrok Pricing](https://ngrok.com/pricing)
- [ngrok Dashboard](https://dashboard.ngrok.com)

## Quick Reference

```bash
# Install
brew install ngrok

# Basic usage
ngrok http 8000

# Auth (for Pro features)
ngrok config add-authtoken TOKEN

# With custom domain (Pro)
ngrok http --domain=myapi.ngrok.io 8000

# Background
ngrok http 8000 &

# Stop
pkill ngrok

# Dashboard
open http://127.0.0.1:4040
```

## Next Steps (Free ngrok)

**For testing Schema Validation only (Free ngrok):**

1. ✅ Install ngrok: `brew install ngrok`
2. ✅ Start services: `docker-compose up -d`
3. ✅ Run ngrok: `ngrok http 8000`
4. ✅ Copy ngrok URL
5. ✅ Set GitHub secret:
   - `REGISTRY_API_URL` = your ngrok URL
6. ✅ Create test PR
7. ✅ Watch schema validation workflow run!
8. ✅ **Remember:** Update secret each time ngrok restarts

**To test both workflows, either:**
- Upgrade to ngrok Pro ($5/month) for multiple tunnels
- Use LocalTunnel or Expose (free alternatives)
- Or test locally in separate terminal (doesn't go through GitHub Actions)