MODE ?=dev
VENV_DIR ?= venv
PYTHON ?= python3
UV ?= $(VENV_DIR)/bin/uv

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make venv        - Create Python virtual environment"
	@echo "  make install     - Install dependencies into venv"
	@echo "  make clean       - Remove virtual environment and temporary files"
	@echo "  make init-db     - Initialize the database"
	@echo "  make seed-db     - Seed the database"
	@echo "  make setup       - Seed the database"
	@echo "  make dev         - Run Flask app in development mode (debug)"
	@echo "  make prod        - Run Flask app in production mode"

# Create virtual environment
.PHONY: venv
venv:
	@echo "Creating virtual environment in $(VENV_DIR)..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment created."

# Install dependencies
.PHONY: install
install: venv
	@echo "Ensuring uv is installed in the venv..."
	$(VENV_DIR)/bin/python -m pip install --upgrade pip
	$(VENV_DIR)/bin/python -m pip install uv
	@echo "Installing project dependencies via uv..."
	$(VENV_DIR)/bin/uv sync
	@echo "Installing dependencies..."
	$(UV) sync
	@echo "Dependencies installed."

# Initialize the database
.PHONY: init-db
init-db:
	$(UV) run flask --app app init-db

# Seed the database
.PHONY: seed-db
seed-db:
	$(UV) run flask --app app seed-db

# Setup the database
.PHONY: setup
setup: init-db seed-db

.PHONY: dev
dev:
	$(UV) run flask --app app run --debug

.PHONY: prod
prod:
	$(UV) run flask --app app run --debug

# Clean up virtual environment and temporary files
.PHONY: clean
clean:
	rm -rf $(VENV_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."
