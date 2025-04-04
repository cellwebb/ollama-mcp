# Changelog

## [Unreleased]

### Added

- Integrated MCP servers into the Ollama-MCP Discord bot.
- Added `MCPClient` class for managing MCP server processes.
- Support for loading MCP server configurations from `mcp.json`.

### Changed

- Updated the main application to start MCP servers before launching the Discord bot.
- Modified the `Session` class to accept an initialized MCP client.
