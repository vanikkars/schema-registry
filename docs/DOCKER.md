# Docker Setup for Registry API

Run the Registry API service in a Docker container using Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- `.env` file with AWS credentials

## Quick Start

### 1. Build and Start

```bash
# Build image and start container
docker-compose up -d

# View logs
docker-compose logs -f registry-api
```

Service runs at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

### 2. Stop

```bash
docker-compose down
```

### 3. Rebuild

```bash
docker-compose build --no-cache
docker-compose up -d
```

## Docker Commands

### Start Service

```bash
# Start in background
docker-compose up -d

# Start with logs
docker-compose up
```

### View Logs

```bash
# Follow logs in real-time
docker-compose logs -f registry-api

# View last 100 lines
docker-compose logs --tail 100 registry-api

# View logs since specific time
docker-compose logs --since 2026-07-26T13:00:00 registry-api
```

### Stop Service

```bash
# Stop container (keeps it)
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove containers, volumes, networks
docker-compose down -v
```

### Check Status

```bash
# View running containers
docker-compose ps

# View container info
docker-compose ps -a
```

### Execute Commands

```bash
# Open shell in running container
docker-compose exec registry-api /bin/bash

# Run Python command in container
docker-compose exec registry-api python -c "print('Hello')"

# List files in container
docker-compose exec registry-api ls -la /app
```

### Build Operations

```bash
# Build image
docker-compose build

# Build without cache
docker-compose build --no-cache

# View built images
docker images | grep schema-registry
```

## Environment Variables

The service reads from `.env` file. Required variables:

```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
```

These are automatically passed to the container via `env_file: .env`

## Volumes

The docker-compose.yml mounts:

- `./contracts:/app/contracts:ro` - Read-only access to contracts
- `./logs:/app/logs` - Logs directory (created on first run)

### Add More Volumes

```yaml
volumes:
  - ./contracts:/app/contracts:ro
  - ./logs:/app/logs
  - ./data:/app/data  # Add custom volume
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

## Health Check

Container includes health check that runs every 30 seconds:

```bash
# Check container health
docker-compose ps

# Should show: "Up X minutes (healthy)"
```

Manual health check:
```bash
curl http://localhost:8000/health
```

## Network

Service runs on network: `schema-registry-net`

Connect other services:
```yaml
services:
  other-service:
    networks:
      - schema-registry-net
    depends_on:
      - registry-api
```

## Usage Examples

### Register Schema via Docker

```bash
# Generate contract first
python contracts_management/generate_contract.py

# Register via API running in Docker
curl -X POST "http://localhost:8000/api/v1/schemas/register" \
  -H "Content-Type: application/json" \
  -d @contracts/user_contract.json
```

### View API Docs

```bash
# Open browser
open http://localhost:8000/docs

# Or use curl to list endpoints
curl http://localhost:8000/api/v1/schemas/list
```

### Run Tests Against Docker Container

```bash
# Wait for container to be ready
docker-compose up -d
sleep 5

# Run API tests
python -m pytest tests/test_api.py --live-server http://localhost:8000
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs registry-api

# Common issues:
# - AWS credentials not set in .env
# - Port 8000 already in use
# - Insufficient permissions
```

### Port Already in Use

```bash
# Change port in docker-compose.yml
# ports:
#   - "8001:8000"

# Or kill existing process
lsof -i :8000
kill -9 <PID>
```

### AWS Credentials Error

```bash
# Verify .env exists
ls -la .env

# Check credentials are set
grep AWS .env

# Ensure .env is in same directory as docker-compose.yml
```

### Container Exits Immediately

```bash
# Check logs
docker-compose logs registry-api

# Common causes:
# - Python syntax error
# - Missing dependencies
# - Import error
```

### Slow Startup

```bash
# Increase start_period in docker-compose.yml
healthcheck:
  start_period: 30s  # Increase from 10s
```

## Performance

### Resource Limits

Add resource limits to docker-compose.yml:

```yaml
services:
  registry-api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

Restart to apply:
```bash
docker-compose down
docker-compose up -d
```

### Optimization Tips

1. **Use .dockerignore** - Excludes unnecessary files from build context
2. **Layer caching** - Docker caches layers, rebuild is faster
3. **Alpine Linux** - Use `python:3.10-alpine` for smaller image
4. **Multi-stage builds** - Reduce final image size

## Production Deployment

### Security

1. **Don't use .env in production** - Use secrets management:

```yaml
services:
  registry-api:
    environment:
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
    secrets:
      - aws_key
      - aws_secret

secrets:
  aws_key:
    external: true
  aws_secret:
    external: true
```

Create secrets:
```bash
echo "your-key" | docker secret create aws_key -
echo "your-secret" | docker secret create aws_secret -
```

2. **Use private registry** - Push to AWS ECR or Docker Hub
3. **Sign images** - Use Docker Content Trust
4. **Scan for vulnerabilities** - Use Trivy or similar

### High Availability

For production, use Docker Swarm or Kubernetes:

```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml schema-registry

# Kubernetes (convert docker-compose to K8s)
kompose convert -f docker-compose.yml -o k8s.yaml
kubectl apply -f k8s.yaml
```

## Logging

### View Logs

```bash
# All logs
docker-compose logs

# Service logs
docker-compose logs registry-api

# Follow mode
docker-compose logs -f

# Show timestamps
docker-compose logs --timestamps
```

### Log Rotation

Add to docker-compose.yml:

```yaml
services:
  registry-api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Debugging

### Interactive Shell

```bash
# Open bash in container
docker-compose exec registry-api /bin/bash

# Run Python interactively
docker-compose exec registry-api python

# Run commands
docker-compose exec registry-api python -m pip list
```

### Inspect Container

```bash
# View container filesystem
docker-compose exec registry-api ls -la

# Check environment variables
docker-compose exec registry-api env

# View running processes
docker-compose exec registry-api ps aux
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker-compose build
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Run tests
        run: |
          docker-compose exec -T registry-api pytest tests/
      
      - name: Stop services
        run: docker-compose down
```

## Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Full cleanup (WARNING: removes everything unused)
docker system prune -a --volumes
```

## See Also

- [README.md](../README.md) - Main documentation
- [registry-api/README.md](../registry-api/README.md) - API service docs
- [API_USAGE.md](API_USAGE.md) - API usage guide
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)