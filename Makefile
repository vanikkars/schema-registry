.PHONY: help docker-build docker-up docker-down docker-logs docker-shell docker-dev docker-dev-down docker-clean test

help:
	@echo "Schema Registry - Make Commands"
	@echo "================================"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build    - Build Docker image"
	@echo "  make docker-up       - Start services (production)"
	@echo "  make docker-down     - Stop services"
	@echo "  make docker-logs     - View service logs"
	@echo "  make docker-shell    - Open shell in container"
	@echo "  make docker-ps       - Show running containers"
	@echo "  make docker-clean    - Clean up Docker resources"
	@echo ""
	@echo "Development Commands:"
	@echo "  make docker-dev      - Start development services (with postgres, redis)"
	@echo "  make docker-dev-down - Stop development services"
	@echo ""
	@echo "Local Commands:"
	@echo "  make setup           - Setup local environment"
	@echo "  make run-api         - Run API locally"
	@echo "  make generate        - Generate contracts"
	@echo "  make test            - Run tests"
	@echo ""

# Docker Production Commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "✅ Services started"
	@echo "📍 API: http://localhost:8000"
	@echo "📖 Docs: http://localhost:8000/docs"

docker-down:
	docker-compose down
	@echo "✅ Services stopped"

docker-logs:
	docker-compose logs -f registry_api

docker-shell:
	docker-compose exec registry_api /bin/bash

docker-ps:
	docker-compose ps

docker-clean:
	docker-compose down -v
	docker system prune -f
	@echo "✅ Docker cleaned"

# Development Commands
docker-dev:
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Development services started"
	@echo "📍 API: http://localhost:8000"
	@echo "📖 Docs: http://localhost:8000/docs"
	@echo "🗄️  PostgreSQL: localhost:5432"
	@echo "💾 Redis: localhost:6379"

docker-dev-down:
	docker-compose -f docker-compose.dev.yml down
	@echo "✅ Development services stopped"

docker-dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Local Commands
setup:
	source .env
	@echo "✅ Environment loaded"

run-api:
	source .env
	bash registry_api/run.sh

generate:
	python contracts_management/generate_contract.py

test:
	source .env
	docker-compose exec registry_api pytest tests/ -v

# Check Commands
check-env:
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
		grep -E "AWS_" .env | head -3; \
	else \
		echo "❌ .env file not found"; \
		echo "   Run: cp .env.example .env"; \
	fi

check-docker:
	@docker --version
	@docker-compose --version
	@echo "✅ Docker is installed"

check-aws:
	@if [ -n "$$AWS_ACCESS_KEY_ID" ]; then \
		echo "✅ AWS credentials loaded"; \
	else \
		echo "⚠️  AWS credentials not loaded"; \
		echo "   Run: source .env"; \
	fi

# Info Commands
info:
	@echo "Schema Registry Project Info"
	@echo "============================"
	@docker-compose ps
	@echo ""
	@echo "Recent Images:"
	@docker images | grep schema-registry || echo "No images found"

version:
	@grep -E "version|VERSION" docker-compose.yml | head -1

# Useful Shortcuts
list-endpoints:
	@echo "API Endpoints:"
	@echo "=============="
	@curl -s http://localhost:8000/docs | grep -o '"operationId":"[^"]*"' | cut -d'"' -f4 || echo "API not running. Run: make docker-up"

health:
	@curl -s http://localhost:8000/health || echo "❌ API not responding"

register-user-schema:
	curl -X POST "http://localhost:8000/api/v1/schemas/register" \
		-H "Content-Type: application/json" \
		-d @contracts/user_contract.json

list-schemas:
	curl "http://localhost:8000/api/v1/schemas/list"

list-all-commands:
	@echo "All available targets:"
	@grep -E "^[a-zA-Z_-]+:" Makefile | sed 's/:.*//g' | column