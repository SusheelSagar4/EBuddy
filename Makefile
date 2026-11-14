# ==============================================================================
# Makefile - Personalised Learning Buddy (IIT Bhubaneswar)
# Commands: up, down, reset, test, conformance, check-data, lint, ci, new-persona, eval, status, logs
# ==============================================================================

.PHONY: up down reset test conformance check-data check-data-release lint ci new-persona eval status logs

up:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; fi
	docker compose up -d db adminer
	@echo "Services started:"
	@echo "  DB:      127.0.0.1:5432"
	@echo "  Adminer: http://localhost:8080"

down:
	docker compose down

reset:
	@echo "Resetting database to initial clean state with seeds..."
	@python scripts/seed_loader.py --reset
	@echo "Database reset complete."

test:
	pytest tests -v

conformance:
	python scripts/run_conformance.py

check-data:
	python scripts/check_data.py

check-data-release:
	python scripts/check_data.py --release

lint:
	pytest tests/unit/test_import_boundaries.py -v

ci:
	./scripts/ci.sh

new-persona:
	@read -p "Enter persona id: " pid; ./scripts/new_persona.sh $$pid

eval:
	python scripts/run_evaluation.py

status:
	docker compose ps

logs:
	docker compose logs -f
