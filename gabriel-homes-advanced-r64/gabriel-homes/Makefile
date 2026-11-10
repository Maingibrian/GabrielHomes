# Gabriel Homes — Makefile of common commands
# Usage: make <target>

.PHONY: help install dev test test-cov lint check deploy-check gate \
	migrate makemigrations seed seed-clear seed-no-images \
	collectstatic runserver shell superuser \
	backup-db restore-db clean

PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
MANAGE := $(VENV)/bin/python manage.py

# Fall back to system python if venv doesn't exist
ifeq (,$(wildcard $(VENV)))
	PIP := pip3
	PY := python3
	MANAGE := python3 manage.py
endif

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	        awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Create venv and install dependencies
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "✓ Dependencies installed. Activate with: source $(VENV)/bin/activate"

dev: install ## Full dev setup: install + migrate + seed
	cp -n .env.example .env || true
	$(MANAGE) migrate
	$(MANAGE) seed_demo
	@echo ""
	@echo "✓ Dev environment ready. Run with: make runserver"

test: ## Run the test suite
	$(MANAGE) test -v 1 || $(PY) -m pytest -q

test-cov: ## Run tests with coverage report
	$(PY) -m pytest --cov=apps --cov-report=term-missing -q

lint: ## Run linters (placeholder — no linter in dev tooling; see DECISIONS.md)
	@echo "No linter configured. Add flake8 or ruff to dev tooling with a DECISIONS.md entry first."

check: ## Run Django system check
	$(MANAGE) check

gate: ## Run the full release gate (scripts/gate.sh — check, migrations, tests, G-DEPLOY, G-SAFE, G-CDN, G-STATIC)
	bash scripts/gate.sh

deploy-check: ## Run check --deploy (uses prod settings + dummy env)
	DJANGO_SETTINGS_MODULE=config.settings.prod \
	SECRET_KEY=dummy-key-for-deploy-check-only-not-for-real-use-1234567890 \
	ALLOWED_HOSTS=localhost \
	$(MANAGE) check --deploy

migrate: ## Apply migrations
	$(MANAGE) migrate

makemigrations: ## Generate migrations
	$(MANAGE) makemigrations

makemigrations-check: ## Check for missing migrations (CI gate)
	$(MANAGE) makemigrations --check --dry-run

seed: ## Seed demo data (with images)
	$(MANAGE) seed_demo

seed-clear: ## Clear + re-seed demo data
	$(MANAGE) seed_demo --clear

seed-no-images: ## Seed demo data without images (faster)
	$(MANAGE) seed_demo --no-images

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

runserver: ## Start the dev server
	$(MANAGE) runserver

shell: ## Django shell
	$(MANAGE) shell

superuser: ## Create a superuser
	$(MANAGE) createsuperuser

backup-db: ## Backup the database via scripts/backup-db.sh (reads DATABASE_URL, MariaDB, keeps 30 days)
	bash scripts/backup-db.sh

restore-drill: ## Restore-drill: newest backup into a scratch DB, run checks, drop (PLAN D5)
	bash scripts/restore-drill.sh

restore-db: ## Restore the database from a backup file (usage: make restore-db FILE=backups/xxx.sql.gz)
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore-db FILE=backups/xxx.sql.gz"; exit 1; fi
	gunzip -c $(FILE) | mariadb -u gabriel -p -h localhost gabriel_homes
	@echo "✓ Restored from $(FILE)"

clean: ## Remove caches + temp files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf staticfiles
	@echo "✓ Cleaned"
