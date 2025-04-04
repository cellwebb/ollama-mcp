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
	python -m venv .venv
	.venv/bin/uv pip install -r requirements.txt
	.venv/bin/uv pip install -r dev-requirements.txt

run:
	@echo "Starting Ollama-MCP Discord bot..."
	python -m ollama_mcp_discord

test:
	@echo "Running tests..."
	python -m pytest tests/

test-cov:
	@echo "Running tests with coverage..."
	python -m pytest --cov=ollama_mcp_discord tests/ --cov-report=term --cov-report=html

lint:
	@echo "Running linters..."
	python -m black --check ollama_mcp_discord tests
	python -m isort --check ollama_mcp_discord tests
	python -m flake8 ollama_mcp_discord tests
	python -m mypy ollama_mcp_discord

format:
	@echo "Formatting code..."
	python -m black ollama_mcp_discord tests
	python -m isort ollama_mcp_discord tests

clean:
	@echo "Removing cache files..."
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf __pycache__
	rm -rf ollama_mcp_discord/__pycache__
	rm -rf tests/__pycache__
	find . -name "*.pyc" -delete 