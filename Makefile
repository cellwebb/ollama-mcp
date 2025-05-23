.PHONY: help test test-cov lint format run clean setup

# Default target executed when no arguments are given to make
default: help

help:
	@echo "Available commands:"
	@echo "  make setup      Create a virtual environment and install dependencies"
	@echo "  make run        Run the Discord bot"
	@echo "  make test       Run unit tests"
	@echo "  make test-cov   Run tests with coverage report"
	@echo "  make lint       Run linters (black, isort, flake8, mypy)"
	@echo "  make format     Format code with black and isort"
	@echo "  make clean      Remove build and cache files"

setup:
	@echo "Setting up virtual environment and installing dependencies..."
	uv venv
	uv pip install .

setup-dev:
	@echo "Setting up virtual environment and installing dependencies for development..."
	uv venv
	uv pip install -e.[dev]

run:
	@echo "Starting Ollama-MCP Discord bot..."
	if [ ! -d ".venv" ]; then \
		echo "Please run 'uv venv' to create a virtual environment."; \
		exit 1; \
	fi
	uv run -- python -m ollama_mcp_discord

test:
	@echo "Running tests..."
	if [ ! -d ".venv" ]; then \
		echo "Please run 'uv venv' to create a virtual environment."; \
		exit 1; \
	fi
	uv run -- pytest tests/

test-cov:
	@echo "Running tests with coverage..."
	if [ ! -d ".venv" ]; then \
		echo "Please run 'uv venv' to create a virtual environment."; \
		exit 1; \
	fi
	uv run -- pytest --cov=ollama_mcp_discord tests/

lint:
	@echo "Running linters..."
	uv pip install .[dev]
	npx prettier --ignore-path=".venv/" "**/*.{md,yaml,yml,json}"
	uv run -- black . --line-length 120
	uv run -- isort .
	uv run -- mypy ollama_mcp_discord
	uv run -- flake8 --max-line-length=120 --exclude=tests/ --ignore=E501 ollama_mcp_discord

format:
	@echo "Formatting code..."
	npx prettier --ignore-path=".venv/" "**/*.{md,yaml,yml,json}"
	uv pip install .[dev]
	uv run -- black . --line-length 120
	uv run -- isort .

clean:
	@echo "Removing cache files..."
	rm -rf .venv
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
