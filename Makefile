# ==============================================================================
# Personalised Learning Buddy (IIT Bhubaneswar)
# ==============================================================================
.PHONY: up down reset reset-local test conformance verify-profiles check-data lint ci profiles tracks new-persona eval status logs

up:            ## start the whole stack (db + adminer + app)
	docker compose up -d --build
	@echo "Web app : http://localhost:8000/app/"
	@echo "Adminer : http://localhost:8080  (server db, user ebuddy_user, password ebuddy_password, database ebuddy)"

down:
	docker compose down

reset:         ## restore the database AND the running app to the original seed state
	docker compose exec app python scripts/seed_loader.py --reset
	@echo "Database reset. The running app drops its in-memory state within about 2 seconds."

reset-local:   ## same, against a local PostgreSQL (no Docker)
	python scripts/seed_loader.py --reset

test:
	python -m pytest tests -q

conformance:
	python scripts/run_conformance.py

verify-profiles: ## prove all 75 profiles get valid, constraint-compliant multi-semester plans
	python scripts/verify_all_75_profiles.py

check-data:
	python scripts/check_data.py

lint:
	python -m pytest tests/unit/test_import_boundaries.py -q

ci:
	./scripts/ci.sh

profiles:      ## regenerate the 75 synthetic profiles (deterministic)
	python scripts/generate_75_student_profiles.py

tracks:        ## rebuild the SDE / DA / AI-ML track CSVs from their workbooks
	python sde/scripts/build_sde_csvs.py && python sde/scripts/build_sde_events_csvs.py && python sde/scripts/build_sde_quiz_csvs.py
	python da/scripts/build_da_csvs.py && python da/scripts/build_da_events_csvs.py && python da/scripts/build_da_quiz_csvs.py
	python aiml/scripts/build_csvs.py && python aiml/scripts/build_events_csvs.py

new-persona:
	@read -p "Enter persona id: " pid; ./scripts/new_persona.sh $$pid

eval:
	python scripts/evaluate_scorecard.py

status:
	docker compose ps

logs:
	docker compose logs -f
