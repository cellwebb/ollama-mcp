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

run:
	@echo "Starting Ollama-MCP Discord bot..."
	python -m ollama_mcp_discord

test:
	@echo "Running tests..."
	uv pip install .[dev]
	uv run -- pytest tests/

test-cov:
	@echo "Running tests with coverage..."
	uv pip install .[dev]
	uv run -- pytest --cov=ollama_mcp_discord tests/

lint:
	@echo "Running linters..."
	uv pip install .[dev]
	uv run -- black .
	uv run -- isort .
	uv run -- mypy ollama_mcp_discord
	uv run -- flake8 ollama_mcp_discord tests

format:
	@echo "Formatting code..."
	uv pip install .[dev]
	black .
	isort .

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