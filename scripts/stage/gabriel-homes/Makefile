# Gabriel Homes — Makefile of common commands
# Usage: make <target>

.PHONY: help install dev test test-cov lint check deploy-check \
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

lint: ## Run linters (placeholder — add flake8/ruff as needed)
	@echo "No linter configured. Add flake8 or ruff to requirements.txt."

check: ## Run Django system check
	$(MANAGE) check

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

backup-db: ## Backup the database (pg_dump)
	@mkdir -p backups
	pg_dump -U gabriel -h localhost gabriel_homes | gzip > backups/gabriel-homes-$$(date +%Y%m%d-%H%M%S).sql.gz
	@echo "✓ Backup saved to backups/"

restore-db: ## Restore the database from a backup file (usage: make restore-db FILE=backups/xxx.sql.gz)
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore-db FILE=backups/xxx.sql.gz"; exit 1; fi
	gunzip -c $(FILE) | psql -U gabriel -h localhost gabriel_homes
	@echo "✓ Restored from $(FILE)"

clean: ## Remove caches + temp files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf staticfiles
	@echo "✓ Cleaned"
