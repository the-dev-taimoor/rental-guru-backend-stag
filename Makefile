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
	@echo "make run            - Run the Django development server"
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

run:
	$(MANAGE) runserver 0.0.0.0:8000

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

lint:
	flake8 apps/ config/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info

# ---------------------------
# Database utilities
# ---------------------------

showmigrations:
	$(MANAGE) showmigrations

sqlmigrate:
	$(MANAGE) sqlmigrate $(app) $(migration)

