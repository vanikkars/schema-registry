# Iceberg Service - Quick Start Guide

## 🎯 Get Running in 5 Minutes

### Prerequisites

- Python 3.11+
- AWS credentials configured
- Docker & Docker Compose (recommended)

### Option 1: Run Locally with Docker Compose (Easiest)

```bash
# Start all services (Schema Registry + Iceberg Service)
docker-compose up -d

# Check services are running
curl http://localhost:8000/health  # Schema Registry
curl http://localhost:8001/health  # Iceberg Service

# View logs
docker-compose logs -f iceberg-creation
```

### Option 2: Run with Python

```bash
# Install dependencies
pip install -r requirements-iceberg.txt

# Start the service
uvicorn iceberg_creation_service.main:app --host 0.0.0.0 --port 8001

# In another terminal, test it
curl http://localhost:8001/health
```

## 📝 Create Your First Table

### 1. Test with a Sample Contract

```bash
curl -X POST http://localhost:8001/api/v1/tables \
  -H "Content-Type: application/json" \
  -d '{
    "contract_id": "users_v1",
    "name": "users",
    "version": 1,
    "description": "User data",
    "columns": [
      {
        "name": "user_id",
        "data_type": "string",
        "description": "Unique user ID"
      },
      {
        "name": "email",
        "data_type": "string"
      },
      {
        "name": "created_at",
        "data_type": "timestamp"
      }
    ],
    "metadata": {
      "data_owner": "my-team",
      "data_steward": "john@company.com"
    }
  }'
```

### 2. Expected Response (201 Created)

```json
{
  "data": {
    "status": "created",
    "table_name": "users_v1",
    "database_name": "iceberg_tables",
    "s3_location": "s3://iceberg-data-123456789-us-east-1/iceberg_tables/users_v1",
    "message": "Iceberg table 'users_v1' created successfully",
    "warnings": [],
    "errors": []
  }
}
```

### 3. Verify in AWS

```bash
# List tables
aws glue get-tables --database-name iceberg_tables

# Get table details
aws glue get-table --database-name iceberg_tables --name users_v1
```

## 🔄 GitHub Actions Workflow

### 1. Set Up GitHub Secret

```bash
# Go to your GitHub repo → Settings → Secrets and variables → Actions
# Create new secret:
# Name: ICEBERG_SERVICE_URL
# Value: https://your-iceberg-service.example.com
```

### 2. Create/Update Contract and Push

```bash
# Create a new contract file
cat > contracts/current/products/products_v1.json << 'EOF'
{
  "contract_id": "products_v1",
  "name": "products",
  "version": 1,
  "columns": [
    {"name": "product_id", "data_type": "string"},
    {"name": "name", "data_type": "string"},
    {"name": "price", "data_type": "double"}
  ]
}
EOF

# Push to branch
git checkout -b add-products-contract
git add contracts/current/products/products_v1.json
git commit -m "add products data contract"
git push -u origin add-products-contract
```

### 3. Create Pull Request

- Go to GitHub → Create PR
- Workflow automatically runs:
  - ✅ Validates contract
  - ✅ Registers schema
  - ✅ Auto-merges
  - ✅ Creates Iceberg table
- See results in PR comment

### 4. Check Results in PR Comment

```
## 📊 Iceberg Table Creation Results

✅ All Iceberg tables created successfully!

| Contract | Table | Status | Details |
|----------|-------|--------|---------|
| products | products_v1 | ✅ CREATED | Iceberg table 'products_v1' created successfully |

---
🎉 Iceberg tables are ready to use!
```

## 🚢 Deploy to Production

### Quick Deployment (Docker)

```bash
# Build image
docker build -f iceberg_creation_service/Dockerfile \
  -t iceberg-service:1.0 .

# Push to your registry
docker push your-registry/iceberg-service:1.0

# Run on server/cloud
docker run -d \
  -p 8001:8001 \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
  -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
  your-registry/iceberg-service:1.0
```

### Full Deployment Options

- **Docker** - See above
- **Kubernetes** - See `docs/ICEBERG_DEPLOYMENT.md`
- **AWS ECS Fargate** - See `docs/ICEBERG_DEPLOYMENT.md`
- **AWS Lambda** - Future enhancement

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [ICEBERG_IMPLEMENTATION_SUMMARY.md](./ICEBERG_IMPLEMENTATION_SUMMARY.md) | Overview of changes |
| [ICEBERG_DEPLOYMENT.md](./docs/ICEBERG_DEPLOYMENT.md) | Full deployment guide |
| [ICEBERG_IMPLEMENTATION.md](./docs/ICEBERG_IMPLEMENTATION.md) | Technical architecture |
| [iceberg_creation_service/README.md](./iceberg_creation_service/README.md) | Service-specific docs |

## 🧪 Common Tasks

### Test Table Creation

```bash
# Basic test
curl -X POST http://localhost:8001/api/v1/tables \
  -H "Content-Type: application/json" \
  -d @contracts/current/user/user_v1.json
```

### Check Service Health

```bash
# Health check
curl http://localhost:8001/health

# Response should be:
# {"status": "ok", "version": "1.0.0"}
```

### Update Table Schema

```bash
# When contract evolves
curl -X POST http://localhost:8001/api/v1/tables/user_v1/schema \
  -H "Content-Type: application/json" \
  -d @contracts/current/user/user_v2.json
```

### Get Table Info

```bash
curl http://localhost:8001/api/v1/tables/user_v1
```

### View Logs

```bash
# Docker
docker logs -f iceberg-creation-service

# Docker Compose
docker-compose logs -f iceberg-creation

# Kubernetes
kubectl logs -f deployment/iceberg-creation-service
```

## 🐛 Troubleshooting

### Service won't start

```bash
# Check if port is in use
lsof -i :8001

# Check AWS credentials
aws sts get-caller-identity

# View error logs
docker logs iceberg-creation-service
```

### Table creation fails

```bash
# Test service is running
curl http://localhost:8001/health

# Check AWS Glue access
aws glue get-databases

# Check service logs for error details
docker logs iceberg-creation-service | grep ERROR
```

### GitHub workflow fails

1. Check GitHub Actions logs:
   - Go to repo → Actions tab
   - Click failed workflow run
   - Check step logs for errors

2. Common issues:
   - `ICEBERG_SERVICE_URL` secret not set
   - Service not accessible from GitHub (firewall/security groups)
   - AWS credentials expired
   - Service not running

## 📊 Supported Data Types

| AVRO Type | Glue Type |
|-----------|-----------|
| string | string |
| int | int |
| long | bigint |
| float | float |
| double | double |
| boolean | boolean |
| bytes | binary |
| date | date |
| timestamp | timestamp |

## ✅ Checklist

- [ ] Service running locally (docker-compose up)
- [ ] Can create test table via curl
- [ ] AWS Glue shows created table
- [ ] Service deployed to production
- [ ] GitHub secret `ICEBERG_SERVICE_URL` configured
- [ ] Test PR created and workflow passed
- [ ] Table visible in PR comment
- [ ] Monitoring/alerting configured

## 🆘 Need Help?

1. **Service Documentation**: See `iceberg_creation_service/README.md`
2. **Architecture Details**: See `docs/ICEBERG_IMPLEMENTATION.md`
3. **Deployment Help**: See `docs/ICEBERG_DEPLOYMENT.md`
4. **GitHub Issues**: Check GitHub repo issues/discussions

## 🚀 Next Steps

1. Test locally with docker-compose ✅
2. Deploy to your environment
3. Configure GitHub secret
4. Test with real PR
5. Monitor production usage
6. Scale as needed

---

**Version**: 1.0.0  
**Last Updated**: 2026-08-01  
**Status**: Production Ready ✨