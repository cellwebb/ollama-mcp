# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Shared HTTP client using HTTPX for connection pooling
- Pydantic-based settings management replacing manual config
- LangChain integration for conversation management (planned)
- Enhanced process management with python-daemon (planned)
- Structured logging with structlog (planned)

### Changed

- Refactored Ollama client to use shared HTTP client
- Updated dependencies to include modern libraries
- Improved environment variable handling with Pydantic
- Reduced custom code in favor of established libraries

## [0.1.0] - 2023-04-04

### Added

- Initial release
- Discord bot with Ollama integration
- MCP server support
- Basic conversation management
