# Iceberg Table Creation Service - Deployment Guide

This guide covers deploying the Iceberg Table Creation Service in various environments.

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- AWS credentials configured

### Option 1: Direct Python

```bash
# Install dependencies
pip install -r requirements-iceberg.txt

# Run the service
uvicorn iceberg_creation_service.main:app --host 0.0.0.0 --port 8001 --reload
```

### Option 2: Docker

```bash
# Using docker-compose
docker-compose up -d iceberg-creation

# Check service is running
curl http://localhost:8001/health
```

## Production Deployment

### AWS Credentials Setup

The service requires AWS credentials to access Glue and STS APIs.

#### Option 1: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

#### Option 2: IAM Role (Recommended)

Attach this policy to your EC2/ECS/Lambda role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:CreateDatabase",
        "glue:CreateTable",
        "glue:UpdateTable",
        "glue:GetTable",
        "glue:GetDatabase",
        "glue:BatchCreatePartition"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    }
  ]
}
```

### GitHub Actions Secrets

Configure these secrets in your GitHub repository:

1. `ICEBERG_SERVICE_URL` - URL to the deployed service (e.g., `https://iceberg.example.com`)

Then in your workflow, the service URL is automatically available:

```yaml
env:
  ICEBERG_SERVICE_URL: ${{ secrets.ICEBERG_SERVICE_URL }}
```

## Deployment Options

### Option 1: Docker Container (Simplest)

```bash
# Build the image
docker build -f iceberg_creation_service/Dockerfile \
  -t your-registry/iceberg-creation-service:1.0 .

# Push to registry
docker push your-registry/iceberg-creation-service:1.0

# Run the container
docker run -d \
  -p 8001:8001 \
  -e AWS_ACCESS_KEY_ID=your-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret \
  -e AWS_DEFAULT_REGION=us-east-1 \
  your-registry/iceberg-creation-service:1.0
```

### Option 2: Docker Compose (Local Dev + Staging)

```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f iceberg-creation

# Stop services
docker-compose down
```

### Option 3: Kubernetes (Recommended for Scale)

#### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Docker image pushed to registry

#### Deployment

**File: `deploy/iceberg-service.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: iceberg-config
  namespace: default
data:
  AWS_DEFAULT_REGION: us-east-1
  ICEBERG_AWS_GLUE_DATABASE: iceberg_tables

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iceberg-creation-service
  namespace: default
  labels:
    app: iceberg-creation
    version: "1.0"
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: iceberg-creation
  template:
    metadata:
      labels:
        app: iceberg-creation
    spec:
      serviceAccountName: iceberg-service-account
      containers:
      - name: iceberg-service
        image: your-registry/iceberg-creation-service:1.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8001
          name: http
        envFrom:
        - configMapRef:
            name: iceberg-config
        env:
        - name: AWS_ROLE_ARN
          value: arn:aws:iam::ACCOUNT:role/iceberg-service-role
        - name: AWS_WEB_IDENTITY_TOKEN_FILE
          value: /var/run/secrets/eks.amazonaws.com/serviceaccount/token
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 2
        securityContext:
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          allowPrivilegeEscalation: false
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: iceberg-creation-service
  namespace: default
  labels:
    app: iceberg-creation
spec:
  type: ClusterIP
  selector:
    app: iceberg-creation
  ports:
  - port: 8001
    targetPort: 8001
    protocol: TCP
    name: http

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: iceberg-service-account
  namespace: default

---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: iceberg-creation-pdb
  namespace: default
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: iceberg-creation
```

Deploy:

```bash
# Create namespace (optional)
kubectl create namespace schema-registry

# Deploy service
kubectl apply -f deploy/iceberg-service.yaml

# Verify deployment
kubectl get pods -l app=iceberg-creation
kubectl logs -f deployment/iceberg-creation-service

# Port forward for local testing
kubectl port-forward svc/iceberg-creation-service 8001:8001
```

### Option 4: AWS ECS Fargate (Recommended for AWS)

**File: `infra/aws/ecs/main.tf`**

```hcl
resource "aws_ecs_cluster" "iceberg" {
  name = "iceberg-creation-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "iceberg" {
  family                   = "iceberg-creation-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "iceberg-service"
      image     = "${aws_ecr_repository.iceberg.repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8001
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "AWS_DEFAULT_REGION"
          value = "us-east-1"
        },
        {
          name  = "ICEBERG_AWS_GLUE_DATABASE"
          value = "iceberg_tables"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.iceberg.name
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "iceberg" {
  name            = "iceberg-creation-service"
  cluster         = aws_ecs_cluster.iceberg.id
  task_definition = aws_ecs_task_definition.iceberg.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.iceberg.arn
    container_name   = "iceberg-service"
    container_port   = 8001
  }

  depends_on = [
    aws_lb_listener.iceberg,
    aws_iam_role_policy.ecs_task_role_policy,
  ]
}

# ALB for load balancing
resource "aws_lb" "iceberg" {
  name               = "iceberg-creation-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids
}

resource "aws_lb_listener" "iceberg" {
  load_balancer_arn = aws_lb.iceberg.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_certificate_arn = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.iceberg.arn
  }
}

resource "aws_lb_target_group" "iceberg" {
  name        = "iceberg-creation-tg"
  port        = 8001
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }
}

# CloudWatch Logs
resource "aws_cloudwatch_log_group" "iceberg" {
  name              = "/ecs/iceberg-creation-service"
  retention_in_days = 7
}
```

Deploy:

```bash
terraform plan
terraform apply
```

## GitHub Actions Configuration

### 1. Create GitHub Secret

1. Go to repository Settings → Secrets and variables → Actions
2. Create new secret: `ICEBERG_SERVICE_URL`
3. Set value to your service URL (e.g., `https://iceberg.example.com`)

### 2. Workflow Usage

The workflow is already configured in `.github/workflows/iceberg-table-creation.yml`.

It automatically runs after schema validation succeeds and posts results to PR.

## Monitoring & Observability

### Logs

```bash
# Docker
docker logs -f iceberg-creation-service

# Kubernetes
kubectl logs -f deployment/iceberg-creation-service

# ECS Fargate (CloudWatch)
aws logs tail /ecs/iceberg-creation-service --follow
```

### Metrics

The service logs:
- Table creation events
- Schema updates with change details
- Errors with full stack traces

### Health Checks

```bash
curl https://your-iceberg-service/health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Scaling Considerations

### Horizontal Scaling

The service is stateless and can be scaled horizontally:

- Kubernetes: Increase `replicas` in deployment
- ECS: Increase `desired_count` in service
- Docker: Run multiple containers with load balancer

### Performance

- Single container: ~100-200 tables/minute
- Typical PR: 5-10 tables, takes ~15-30 seconds total

### Cost Estimation (AWS)

- **ECS Fargate (256 CPU/512 MB)**: ~$15/month
- **Data Transfer**: Minimal (Glue API calls only)
- **CloudWatch Logs**: ~$0.50/month for typical volume
- **Total**: ~$15-20/month

## Troubleshooting

### Service won't start

```bash
# Check logs
docker logs iceberg-creation-service

# Common issues:
# - Port 8001 already in use
# - Missing AWS credentials
# - Dependency failure
```

### AWS Permission Denied

Verify IAM role has required permissions:

```bash
# Test credentials
aws sts get-caller-identity

# Test Glue access
aws glue get-databases --region us-east-1
```

### GitHub Actions can't reach service

1. Verify service is accessible from GitHub (public IP or GitHub runners)
2. Check security groups allow port 443 inbound
3. Verify `ICEBERG_SERVICE_URL` secret is set correctly
4. Check service is running: `curl https://your-service/health`

## Rollback Procedures

### Docker

```bash
docker pull your-registry/iceberg-creation-service:previous-version
docker run -d -p 8001:8001 your-registry/iceberg-creation-service:previous-version
```

### Kubernetes

```bash
kubectl rollout history deployment/iceberg-creation-service
kubectl rollout undo deployment/iceberg-creation-service
```

### ECS

```bash
aws ecs describe-services --cluster iceberg-creation-cluster \
  --services iceberg-creation-service
aws ecs update-service --cluster iceberg-creation-cluster \
  --service iceberg-creation-service \
  --task-definition iceberg-creation-service:previous-version
```

## Backup & Recovery

No backup needed (service is stateless). All table definitions are in:
- AWS Glue Schema Registry
- GitHub repository (contracts/)

To recover:
1. Redeploy service
2. Re-run GitHub Actions workflow for missed tables