# Using ngrok to Expose Local Registry API for GitHub Actions

When running your registry API locally on `localhost:8000`, GitHub Actions running in the cloud cannot reach it. **ngrok** exposes your local API to the internet so GitHub Actions can validate contracts.

## What is ngrok?

**ngrok** creates a secure tunnel from your local machine to the internet, allowing external services (like GitHub Actions) to reach your local API.

```
Your PC (localhost:8000)
    ↑
    │ ngrok tunnel
    │
Internet
    ↑
    │
GitHub Actions
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

### Step 1: Start Your Registry API
```bash
make docker-up
# API is now running on http://localhost:8000
```

### Step 2: Expose with ngrok (new terminal)
```bash
ngrok http 8000
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
```
https://abc123def456.ngrok.io
```

### Step 4: Set GitHub Secret
1. Go to GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `REGISTRY_API_URL`
5. Value: `https://abc123def456.ngrok.io`
6. Click **Add secret**

### Step 5: Create a Test PR
Push a contract change and create a PR. GitHub Actions will now reach your local API!

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

## GitHub Actions Workflow

### Automatic Detection
Once you set the `REGISTRY_API_URL` secret, the workflow automatically uses it:

```yaml
env:
  REGISTRY_API_URL: ${{ secrets.REGISTRY_API_URL || 'http://localhost:8000' }}
```

The workflow:
1. Reads `REGISTRY_API_URL` from GitHub secret
2. Uses it for API calls
3. Posts results to PR

### Testing the Connection
The workflow logs will show:
```
📤 Sending contract to registry...
📍 Registry API: https://abc123def456.ngrok.io
✅ Contract validated
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
# Terminal 1: Start API
make docker-up

# Terminal 2: Start ngrok (keep running)
ngrok http 8000

# Terminal 3: Create PR and watch workflow
# Workflow uses ngrok URL to reach API
```

### 3. Update Secret When URL Changes
If ngrok URL changes, update GitHub secret:
1. Get new URL from ngrok
2. Go to GitHub → Settings → Secrets
3. Update `REGISTRY_API_URL` with new URL
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

Add ngrok to your docker-compose.yml:

```yaml
services:
  registry_api:
    # ... your API config ...
    ports:
      - "8000:8000"

  ngrok:
    image: ngrok/ngrok:latest
    environment:
      - NGROK_AUTHTOKEN=${NGROK_TOKEN}
    command: http registry_api:8000 --domain=myapi.ngrok.io
    ports:
      - "4040:4040"  # Web interface
    depends_on:
      - registry_api
```

Then:
```bash
export NGROK_TOKEN=your_token
docker-compose up
# ngrok automatically starts with API
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

### "Workflow still can't reach API"

**Problem:** GitHub Actions shows "Cannot connect to registry API"

**Solutions:**
1. Check `REGISTRY_API_URL` secret exists in GitHub
2. Verify URL format: `https://xxx.ngrok.io` (HTTPS, not HTTP)
3. Test URL locally: `curl https://abc123def456.ngrok.io/health`
4. Check ngrok logs in web interface (http://127.0.0.1:4040)

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
# Terminal 1: Start API
cd /path/to/schema-registry
make docker-up

# Terminal 2: Start ngrok
ngrok http 8000
# Copy: https://abc123def456.ngrok.io

# Terminal 3: Set GitHub secret (one-time)
# Go to GitHub → Settings → Secrets
# REGISTRY_API_URL = https://abc123def456.ngrok.io

# Terminal 3: Create test PR
git checkout -b test-contract
# Modify a contract
git push origin test-contract
# Open PR on GitHub
# Watch Actions tab!
```

### What Happens
1. ✅ Workflow triggers
2. ✅ Reads GitHub secret
3. ✅ Uses ngrok URL to reach local API
4. ✅ Validates contracts
5. ✅ Posts results to PR
6. ✅ Auto-merges if valid

## Production Deployment

When ready for production:

1. **Deploy API** to cloud (AWS, Heroku, etc.)
2. **Update GitHub secret** with production URL
3. **Remove ngrok** locally
4. **Workflow continues to work** with production API

```bash
# Update secret
REGISTRY_API_URL = https://prod-api.your-domain.com

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
2. ✅ Start API: `make docker-up`
3. ✅ Run ngrok: `ngrok http 8000`
4. ✅ Copy URL and set GitHub secret
5. ✅ Create test PR
6. ✅ Watch it work!