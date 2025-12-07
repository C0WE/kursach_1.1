.PHONY: help build up down logs test clean restart health

help:
	@echo "Available commands:"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - View service logs"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Remove volumes"
	@echo "  make restart      - Restart services"
	@echo "  make health       - Check service health"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	docker-compose run --rm webapp pytest -v

clean:
	docker-compose down -v

restart:
	docker-compose restart

health:
	docker-compose ps
	curl http://localhost/health
