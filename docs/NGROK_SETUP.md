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

### Step 2: Expose Both Services with ngrok (new terminal)

**Option A: Expose both services (Recommended)**
```bash
# Terminal 2a: Expose Registry API
ngrok http 8000 --subdomain=registry-api

# Terminal 2b: Expose Iceberg Service (in another terminal)
ngrok http 8001 --subdomain=iceberg-api
```

**Option B: Expose with dynamic subdomains (Free ngrok)**
```bash
# Terminal 2: Start ngrok (exposes both)
ngrok http 8000
# Note the URL, e.g., https://abc123def456.ngrok.io
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

### Step 3: Copy the HTTPS URLs

For **Registry API**:
```
https://abc123def456.ngrok.io
```

For **Iceberg Service** (if using same ngrok instance):
- If you exposed port 8000, use the same URL but requests will only reach port 8000
- **Recommended**: Use separate ngrok instances for each service
  - Registry API: `https://registry-api.ngrok.io`
  - Iceberg Service: `https://iceberg-api.ngrok.io`

### Step 4: Set GitHub Secrets
1. Go to GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Create first secret:
   - Name: `REGISTRY_API_URL`
   - Value: `https://abc123def456.ngrok.io` (or your ngrok URL)
   - Click **Add secret**
4. Create second secret:
   - Name: `ICEBERG_SERVICE_URL`
   - Value: `https://iceberg-api.ngrok.io` (or your Iceberg service URL)
   - Click **Add secret**

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

### 1. ngrok URL Changes (Free Version)
Free ngrok changes URL every time you restart:
- ❌ URL is temporary
- ✅ Good for testing
- ❌ Bad for production

```bash
# Session 1:
ngrok http 8000
# URL: https://abc123def456.ngrok.io

# Restart...

# Session 2:
ngrok http 8000
# URL: https://xyz789uvw456.ngrok.io (different!)
```

### 2. Keep ngrok Running
ngrok must stay running while you test:

```bash
# Terminal 1: Start services
docker-compose up -d

# Terminal 2a: Start ngrok for Registry API (keep running)
ngrok http 8000

# Terminal 2b: Start ngrok for Iceberg Service (in another terminal, keep running)
ngrok http 8001

# Terminal 3: Create PR and watch workflows
# Workflows use ngrok URLs to reach both services
```

### 3. Update Secrets When URLs Change
If ngrok URLs change, update GitHub secrets:
1. Get new URLs from ngrok terminals
2. Go to GitHub → Settings → Secrets
3. Update:
   - `REGISTRY_API_URL` with new Registry API URL
   - `ICEBERG_SERVICE_URL` with new Iceberg Service URL
4. Create another test PR

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

### Option 4: Docker Compose Integration

Add ngrok services to your docker-compose.yml:

```yaml
services:
  registry_api:
    # ... your API config ...
    ports:
      - "8000:8000"

  iceberg-creation:
    # ... your Iceberg service config ...
    ports:
      - "8001:8001"

  ngrok-registry:
    image: ngrok/ngrok:latest
    environment:
      - NGROK_AUTHTOKEN=${NGROK_TOKEN}
    command: http registry_api:8000 --domain=registry-api.ngrok.io
    ports:
      - "4040:4040"  # Web interface
    depends_on:
      - registry_api

  ngrok-iceberg:
    image: ngrok/ngrok:latest
    environment:
      - NGROK_AUTHTOKEN=${NGROK_TOKEN}
    command: http iceberg-creation:8001 --domain=iceberg-api.ngrok.io
    ports:
      - "4041:4041"  # Web interface
    depends_on:
      - iceberg-creation
```

Then:
```bash
export NGROK_TOKEN=your_token
docker-compose up
# ngrok automatically starts with both services
# Registry API: https://registry-api.ngrok.io
# Iceberg Service: https://iceberg-api.ngrok.io
```

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

## Complete Workflow Example

### Terminal Setup
```bash
# Terminal 1: Start services
cd /path/to/schema-registry
docker-compose up -d

# Terminal 2a: Expose Registry API with ngrok
ngrok http 8000 --subdomain=registry-api
# Copy: https://registry-api.ngrok.io

# Terminal 2b: Expose Iceberg Service with ngrok (in another terminal)
ngrok http 8001 --subdomain=iceberg-api
# Copy: https://iceberg-api.ngrok.io

# Terminal 3: Set GitHub secrets (one-time)
# Go to GitHub → Settings → Secrets
# Create: REGISTRY_API_URL = https://registry-api.ngrok.io
# Create: ICEBERG_SERVICE_URL = https://iceberg-api.ngrok.io

# Terminal 4: Create test PR
git checkout -b test-contract
# Add a new contract file
git add contracts/current/example/example_v1.json
git push origin test-contract
# Open PR on GitHub
# Watch Actions tab!
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

## Next Steps

1. ✅ Install ngrok: `brew install ngrok`
2. ✅ Start services: `docker-compose up -d`
3. ✅ Run ngrok for Registry API: `ngrok http 8000 --subdomain=registry-api`
4. ✅ Run ngrok for Iceberg Service: `ngrok http 8001 --subdomain=iceberg-api`
5. ✅ Copy URLs and set GitHub secrets:
   - `REGISTRY_API_URL`
   - `ICEBERG_SERVICE_URL`
6. ✅ Create test PR
7. ✅ Watch both workflows run!