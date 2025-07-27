# CloudWatch Pro - Makefile
# Ułatwia zarządzanie projektem i wdrażanie

.PHONY: help build up down logs clean test lint format

# Domyślny target
help:
	@echo "CloudWatch Pro - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make build     - Build all Docker images"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make restart   - Restart all services"
	@echo "  make logs      - Show logs from all services"
	@echo "  make logs-f    - Follow logs from all services"
	@echo ""
	@echo "Individual services:"
	@echo "  make up-db     - Start only databases"
	@echo "  make up-api    - Start API services"
	@echo "  make up-frontend - Start frontend"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean     - Remove all containers and volumes"
	@echo "  make prune     - Clean up Docker system"
	@echo "  make backup    - Backup databases"
	@echo "  make restore   - Restore databases"
	@echo ""
	@echo "Development tools:"
	@echo "  make test      - Run all tests"
	@echo "  make lint      - Run linting"
	@echo "  make format    - Format code"
	@echo "  make shell-<service> - Open shell in service container"

# Build all images
build:
	@echo "Building all Docker images..."
	docker-compose build

# Start all services
up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started. Dashboard available at http://localhost:3000"
	@echo "API Gateway available at http://localhost:8000"
	@echo "Grafana available at http://localhost:3001 (admin/admin123)"

# Stop all services
down:
	@echo "Stopping all services..."
	docker-compose down

# Restart all services
restart: down up

# Show logs
logs:
	docker-compose logs

# Follow logs
logs-f:
	docker-compose logs -f

# Start only databases
up-db:
	@echo "Starting databases..."
	docker-compose up -d postgres redis influxdb elasticsearch kafka zookeeper

# Start API services
up-api:
	@echo "Starting API services..."
	docker-compose up -d api-gateway user-service metrics-collector

# Start frontend
up-frontend:
	@echo "Starting frontend..."
	docker-compose up -d dashboard

# Clean everything
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Prune Docker system
prune:
	@echo "Pruning Docker system..."
	docker system prune -af
	docker volume prune -f

# Backup databases
backup:
	@echo "Creating database backups..."
	mkdir -p backups
	docker-compose exec postgres pg_dump -U cloudwatch cloudwatch_users > backups/postgres_$(shell date +%Y%m%d_%H%M%S).sql
	docker-compose exec influxdb influx backup /tmp/backup
	docker cp cloudwatch-influxdb:/tmp/backup backups/influxdb_$(shell date +%Y%m%d_%H%M%S)

# Restore databases (requires backup files)
restore:
	@echo "Restoring databases..."
	@echo "Please specify backup files manually"

# Run tests
test:
	@echo "Running tests..."
	docker-compose exec user-service python -m pytest tests/
	docker-compose exec metrics-collector python -m pytest tests/
	docker-compose exec api-gateway python -m pytest tests/

# Run linting
lint:
	@echo "Running linting..."
	docker-compose exec user-service python -m flake8 .
	docker-compose exec metrics-collector python -m flake8 .
	docker-compose exec api-gateway python -m flake8 .

# Format code
format:
	@echo "Formatting code..."
	docker-compose exec user-service python -m black .
	docker-compose exec metrics-collector python -m black .
	docker-compose exec api-gateway python -m black .

# Shell access to services
shell-user:
	docker-compose exec user-service /bin/bash

shell-metrics:
	docker-compose exec metrics-collector /bin/bash

shell-gateway:
	docker-compose exec api-gateway /bin/bash

shell-postgres:
	docker-compose exec postgres psql -U cloudwatch cloudwatch_users

shell-redis:
	docker-compose exec redis redis-cli

shell-influx:
	docker-compose exec influxdb influx

# Development helpers
dev-setup:
	@echo "Setting up development environment..."
	cp services/user-service/.env.example services/user-service/.env
	cp services/metrics-collector/.env.example services/metrics-collector/.env
	cp services/api-gateway/.env.example services/api-gateway/.env
	@echo "Environment files created. Please review and update them."

# Health check
health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "API Gateway not responding"
	@curl -s http://localhost:8001/health | jq . || echo "User Service not responding"
	@curl -s http://localhost:8002/health | jq . || echo "Metrics Collector not responding"
	@curl -s http://localhost:3000/health || echo "Dashboard not responding"

# Monitor logs for specific service
logs-user:
	docker-compose logs -f user-service

logs-metrics:
	docker-compose logs -f metrics-collector

logs-gateway:
	docker-compose logs -f api-gateway

logs-dashboard:
	docker-compose logs -f dashboard

# Quick development start
dev: up-db
	@echo "Waiting for databases to be ready..."
	@sleep 10
	@make up-api
	@echo "Waiting for API services to be ready..."
	@sleep 5
	@make up-frontend
	@echo "Development environment ready!"

# Production deployment preparation
prod-build:
	@echo "Building production images..."
	docker-compose -f docker-compose.prod.yml build

# Security scan
security-scan:
	@echo "Running security scans..."
	docker run --rm -v $(PWD):/app clair-scanner:latest /app

# Performance test
perf-test:
	@echo "Running performance tests..."
	# Add performance testing commands here

