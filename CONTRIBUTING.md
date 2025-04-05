# Contributing to Ollama-MCP Discord Bot

## Welcome Contributors!

We appreciate your interest in contributing to the Ollama-MCP Discord Bot. This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork
3. Create a virtual environment

   ```bash
   uv venv
   source .venv/bin/activate
   ```

4. Install dependencies

   ```bash
   uv pip install .[dev]
   ```

## Contribution Process

1. Create a new branch for your feature or bugfix

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

   - Follow PEP 8 guidelines
   - Add/update tests for new functionality
   - Ensure all tests pass with `make test`

3. Commit your changes

   - Use descriptive commit messages
   - Reference issue numbers if applicable

4. Push to your fork and submit a Pull Request

## Code Style

- Use `black` for code formatting
- Use `isort` for import sorting
- Maximum line length: 100 characters
- Write docstrings using Google style format
- Add type hints

## Testing

- Write unit tests for new functionality
- Aim for 90%+ test coverage
- Use `pytest` for testing
- Run tests with `make test`

## Documentation

- Update README.md for user-facing changes
- Update ROADMAP.md for significant features
- Keep docstrings clear and informative

## System Message Feature Guidelines

When contributing to the system message functionality:

- Ensure system messages are stored securely
- Validate system message input
- Handle edge cases (empty messages, very long messages)
- Maintain the existing file-based storage mechanism

## Reporting Issues

- Use GitHub Issues
- Provide a clear description
- Include steps to reproduce
- Share relevant error messages or logs

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Collaborate openly and positively

## Questions?

If you have any questions, please open an issue or reach out to the maintainers.
