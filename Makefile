# Production (EC2): everything runs in Docker via compose.yaml + compose.prod.yaml.
#
#   make up                  build images and start / update everything
#   make logs s=api          follow logs (all services if s is omitted)
#   make restart s=voice-1   restart one service
#
# First-time setup:
#   cp .env.example .env                    # DOMAIN
#   cp backend/.env.example backend/.env    # AUTH_SECRET, DB password

COMPOSE := docker compose -f compose.yaml -f compose.prod.yaml
s ?=

.DEFAULT_GOAL := help
.PHONY: help up down restart ps logs build migrate infra dev

help: ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  make %-10s %s\n", $$1, $$2}'

up: ## Build images and start (or update) all services in the background
	$(COMPOSE) up -d --build --remove-orphans

down: ## Stop and remove all containers (data volumes are kept)
	$(COMPOSE) down

restart: ## Restart all services, or one with s=<service>
	$(COMPOSE) restart $(s)

ps: ## Show service status
	$(COMPOSE) ps

logs: ## Follow logs of all services, or one with s=<service>
	$(COMPOSE) logs -f --tail=200 $(s)

build: ## Build images without starting anything
	$(COMPOSE) build

migrate: ## Run database migrations now
	$(COMPOSE) run --rm migrate

infra: ## Local development: start only the infra (db, livekit, jaeger, storage)
	docker compose -f compose.yaml up -d

dev: ## Local development: api (:4000), voice (:4001), frontend (:3000). Run `make infra` first.
	uvx honcho -f Procfile start
