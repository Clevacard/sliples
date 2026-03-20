.PHONY: help up down build logs shell migrate test lint format clean

# Default target
help:
	@echo "Sliples - Web UI Automation Testing Platform"
	@echo ""
	@echo "Usage:"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make build     - Build all containers"
	@echo "  make logs      - View logs (all services)"
	@echo "  make shell     - Open shell in backend container"
	@echo "  make migrate   - Run database migrations"
	@echo "  make test      - Run backend tests"
	@echo "  make lint      - Run linters"
	@echo "  make format    - Format code"
	@echo "  make clean     - Remove containers and volumes"
	@echo ""
	@echo "Service-specific:"
	@echo "  make logs-backend   - View backend logs"
	@echo "  make logs-worker    - View worker logs"
	@echo "  make logs-frontend  - View frontend logs"

# Start all services
up:
	docker compose up -d
	@echo "Services starting..."
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  MinIO:    http://localhost:9001"

# Stop all services
down:
	docker compose down

# Build all containers
build:
	docker compose build

# View logs
logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-worker:
	docker compose logs -f worker

logs-frontend:
	docker compose logs -f frontend

# Open shell in backend
shell:
	docker compose exec backend bash

# Database migrations
migrate:
	docker compose exec backend alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; \
	docker compose exec backend alembic revision --autogenerate -m "$$msg"

# Run tests
test:
	docker compose exec backend pytest -v

test-cov:
	docker compose exec backend pytest --cov=app --cov-report=html

# Linting
lint:
	docker compose exec backend ruff check app/
	docker compose exec frontend npm run lint

# Format code
format:
	docker compose exec backend ruff format app/
	docker compose exec frontend npm run format

# Clean up
clean:
	docker compose down -v --remove-orphans
	rm -rf backend/.pytest_cache
	rm -rf backend/htmlcov
	rm -rf frontend/node_modules/.vite

# Initialize MinIO bucket
init-minio:
	@echo "Creating MinIO bucket..."
	docker compose exec minio mc alias set local http://localhost:9000 sliples sliples_dev
	docker compose exec minio mc mb local/sliples-screenshots --ignore-existing

# Development setup
dev-setup: build up migrate init-minio
	@echo "Development environment ready!"
