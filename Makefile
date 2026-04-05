.PHONY: up down build test test-backend test-frontend lint migrate audit shell-backend

up:
	docker compose up

down:
	docker compose down

build:
	docker compose build

## Tests
test: test-backend test-frontend

test-backend:
	docker compose run --rm backend pytest -x -q --no-header

test-frontend:
	docker compose run --rm frontend npm test

## Calidad de código
lint:
	docker compose run --rm backend ruff check .
	docker compose run --rm backend black --check .
	docker compose run --rm frontend npm run lint

## Base de datos
migrate:
	docker compose run --rm backend alembic upgrade head

## Seguridad de dependencias
audit:
	docker compose run --rm backend pip-audit
	docker compose run --rm frontend npm audit

## Utilidades
shell-backend:
	docker compose exec backend bash
