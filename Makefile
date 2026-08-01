.PHONY: help docker-build docker-up docker-down docker-logs docker-shell docker-dev docker-dev-down docker-clean test validate-contracts validate-all tunnel-setup tunnel-run tunnel-list tunnel-stop

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
	@echo "Tunnel Commands (GitHub Actions Integration):"
	@echo "  make tunnel-run-registry  - Expose Registry API (8000) via tunnel"
	@echo "  make tunnel-run-iceberg   - Expose Iceberg Service (8001) via tunnel"
	@echo "  make tunnel-setup         - Setup named tunnel (for permanent URLs)"
	@echo "  make tunnel-list          - List all Cloudflare Tunnels"
	@echo "  make tunnel-stop          - Stop all Cloudflare Tunnels"
	@echo ""
	@echo "Local Commands:"
	@echo "  make setup           - Setup local environment"
	@echo "  make run-api         - Run API locally"
	@echo "  make generate        - Generate contracts"
	@echo "  make test            - Run tests"
	@echo ""
	@echo "Schema Commands:"
	@echo "  make upload-contract        - Upload a contract (prompts for file)"
	@echo "  make upload-user-contract   - Upload user contract"
	@echo "  make list-schemas           - List all schemas in registry"
	@echo "  make schema-detail          - Get schema details (use SCHEMA_NAME=<name>)"
	@echo "  make health                 - Check API health"
	@echo ""
	@echo "Validation Commands (Contract Automation):"
	@echo "  make validate-contracts     - Validate current contracts (contracts/current/)"
	@echo "  make validate-contracts-all - Validate all contracts (contracts/all/)"
	@echo "  make validate-export        - Validate current and export results"
	@echo "  make validate-export-all    - Validate all and export results"
	@echo "  make validate-remote        - Validate current contracts against remote API"
	@echo ""

# Docker Production Commands
docker-build:
	docker-compose build

docker-up-build:
	docker-compose up --build

docker-up:
	docker-compose up
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
	@echo "❌ Contract generation moved to static contracts/ folder"
	@echo "   Add or modify contracts in: contracts/"

test:
	source .env
	docker-compose exec registry_api pytest tests/ -v


tf-init:
	source .env && cd infra/aws && rm -rf .terraform && rm -rf .terraform.lock.hcl && rm -rf terraform.tfstate && terraform init


tf-plan:
	source .env && cd infra/aws && terraform plan

tf-apply:
	source .env && cd infra/aws && terraform apply

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

upload-contract:
	bash contracts_management/upload_contract.sh

upload-user-contract:
	bash contracts_management/upload_contract.sh contracts/user_contract.json

list-schemas:
	bash contracts_management/list_schemas.sh

schema-detail:
	@echo "Usage: make schema-detail SCHEMA_NAME=<name>"
	@curl -s "http://localhost:8000/api/v1/schemas/detail/$${SCHEMA_NAME}" | jq .

list-all-commands:
	@echo "All available targets:"
	@grep -E "^[a-zA-Z_-]+:" Makefile | sed 's/:.*//g' | column

# Contract Validation Commands
validate-contracts:
	@echo "🔍 Validating current contracts..."
	python scripts/validate-contracts.py contracts/current/

validate-contracts-all:
	@echo "🔍 Validating all contracts..."
	python scripts/validate-contracts.py contracts/all/

validate-contracts-%:
	@echo "🔍 Validating contracts in $*..."
	python scripts/validate-contracts.py contracts/$*

validate-export:
	@echo "🔍 Validating current contracts and exporting results..."
	python scripts/validate-contracts.py contracts/current/ --export validation_results.json
	@echo "✅ Results saved to validation_results.json"

validate-export-all:
	@echo "🔍 Validating all contracts and exporting results..."
	python scripts/validate-contracts.py contracts/all/ --export validation_results.json
	@echo "✅ Results saved to validation_results.json"

validate-remote:
	@echo "🔍 Validating current contracts against remote API..."
	@read -p "Enter registry API URL: " url; \
	python scripts/validate-contracts.py contracts/current/ --registry-url $$url

# Cloudflare Tunnel Commands
tunnel-setup:
	@echo "🚀 Setting up Cloudflare Tunnel..."
	bash scripts/setup-cloudflare-tunnel.sh

tunnel-run-registry:
	@echo "🚀 Starting tunnel for Registry API (8000)..."
	@echo "💡 Tip: Keep this terminal open while developing"
	@echo "⏳ Waiting for tunnel to establish... (may take 10-15 seconds)"
	cloudflared tunnel --url http://127.0.0.1:8000

tunnel-run-iceberg:
	@echo "🚀 Starting tunnel for Iceberg Service (8001)..."
	@echo "💡 Tip: Keep this terminal open while developing"
	@echo "⏳ Waiting for tunnel to establish... (may take 10-15 seconds)"
	cloudflared tunnel --url http://127.0.0.1:8001

tunnel-list:
	@echo "🔍 Cloudflare Tunnels:"
	@cloudflared tunnel list

tunnel-stop:
	@echo "🛑 Stopping Cloudflare Tunnel..."
	@pkill cloudflared || echo "No tunnel running"
	@echo "✅ Tunnel stopped"