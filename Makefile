# ============================================================
# Django Makefile
# Project: Rental Guru
# Usage: run commands like `make run`, `make migrate`, etc.
# ============================================================

# Default Python and manage.py settings
PYTHON := python
MANAGE := $(PYTHON) manage.py
ENV_FILE := .env

# Default environment (can be overridden: `make run ENV=prod`)
ENV ?= local
DJANGO_SETTINGS := config.settings

export DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS)

# ---------------------------
# Helper targets
# ---------------------------

.PHONY: help
help:
	@echo "Django Management Commands"
	@echo "---------------------------"
	@echo "make dev-local      - Run the Django development server"
	@echo "make migrate        - Apply migrations"
	@echo "make makemigrations - Create new migrations"
	@echo "make superuser      - Create a superuser"
	@echo "make shell          - Open Django shell"
	@echo "make test           - Run test suite"
	@echo "make check          - Check for pending migrations"
	@echo "make lint           - Run code linting with flake8"
	@echo "make collectstatic  - Collect static files"
	@echo "make clean          - Remove pycache and build artifacts"
	@echo "make env            - Show current Django environment"

# ---------------------------
# Core Django commands
# ---------------------------

dev-local::
	$(MANAGE) runserver 127.0.0.1:8000

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

check:
	$(MANAGE) makemigrations --check --dry-run

superuser:
	$(MANAGE) createsuperuser

shell:
	$(MANAGE) shell

test:
	$(MANAGE) test

collectstatic:
	$(MANAGE) collectstatic --noinput

# ---------------------------
# Environment and cleanup
# ---------------------------

env:
	@echo "Using Django settings: $(DJANGO_SETTINGS_MODULE)"

# ---------------------------
# Database utilities
# ---------------------------

showmigrations:
	$(MANAGE) showmigrations

sqlmigrate:
	$(MANAGE) sqlmigrate $(app) $(migration)


# Target to clean the Python program cache files and directories
.PHONY: clean
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Target to create new requirements file if any dependency is installed or updated
.PHONY: add-deps
add-deps:
	pip freeze > requirements.txt

# Target to install requirements from a requirements.txt file
.PHONY: install-deps
install-deps:
	pip install -r requirements.txt

# Target to format code using black
.PHONY: format
format:
	black . --preview

# Target to check code using ruff
.PHONY: lint
lint:
	ruff check .

# Target to check and fix code using ruff
.PHONY: lint-fix
lint-fix:
	ruff check --fix .

# Target to install git hooks using pre-commit to check lint and format issues before commit
.PHONY: hooks
hooks:
	pre-commit install
