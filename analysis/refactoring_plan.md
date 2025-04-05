# Refactoring Plan: Ollama-MCP Discord Bot

## Priority 1: Configuration with Pydantic

### Current Issue

The Configuration class uses custom logic for parsing environment variables, with multiple helper methods like `_get_required_env` and `_parse_list_env`.

### Refactoring Steps

1. Replace the current Configuration class with Pydantic BaseSettings model
2. Move environment variable loading to Pydantic
3. Leverage Pydantic's validation and type conversion
4. Use nested models for better organization

### Benefits

- Reduced code: ~100 lines → ~40 lines
- Automatic validation and error messages
- Type checking and conversion
- Better IDE support

## Priority 2: HTTP Client Management with HTTPX

### Current Issue

Multiple client classes (`OllamaClient`, MCP clients) manage their own HTTP sessions with custom lifecycle management.

### Refactoring Steps

1. Create a shared HTTP client module using HTTPX
2. Implement connection pooling and proper lifecycle management
3. Add middleware for common concerns (retries, timeouts, logging)
4. Refactor all API clients to use the shared client

### Benefits

- Single responsibility for HTTP concerns
- Automatic connection pooling
- Better error handling
- Reduced code duplication

## Priority 3: Session Management with LangChain

### Current Issue

Custom `Session` class in `session.py` manages conversation history and context with custom logic.

### Refactoring Steps

1. Integrate LangChain for conversation management
2. Use LangChain Memory classes for history tracking
3. Replace custom prompt construction with LangChain PromptTemplates
4. Leverage LangChain tools for MCP integration

### Benefits

- Industry-standard conversation management
- Better handling of context limits
- Integration with more advanced memory types
- Access to a rich ecosystem of tools

## Priority 4: Process Management with Python Daemon

### Current Issue

Custom process management in `BaseMCPServer` manually handles subprocess creation and termination.

### Refactoring Steps

1. Replace subprocess handling with python-daemon
2. Implement proper daemon lifecycle management
3. Add structured logging for process status
4. Handle graceful shutdown properly

### Benefits

- More reliable process management
- Better handling of edge cases (crashes, hangs)
- Proper daemonization
- Standard logging and monitoring

## Priority 5: API Error Handling Pattern

### Current Issue

Inconsistent error handling across client methods with redundant try/except blocks.

### Refactoring Steps

1. Create standard error types for different failure scenarios
2. Implement error middleware in the HTTP client
3. Use context managers for consistent error handling
4. Add structured error logging

### Benefits

- Consistent error handling
- Better error reporting
- Reduced code duplication
- Easier debugging

## Priority 6: Command Registration with Decorators

### Current Issue

Manual command registration in `bot.py` with boilerplate for each command.

### Refactoring Steps

1. Create a command registration system using decorators
2. Implement automatic help generation
3. Add middleware for command pre/post processing
4. Consolidate error handling for commands

### Benefits

- Reduced boilerplate
- Consistent command handling
- Easier addition of new commands
- Better organization

## Priority 7: Structured Logging with Structlog

### Current Issue

Basic logging setup with limited configuration and structure.

### Refactoring Steps

1. Integrate structlog for structured logging
2. Add context processors for request/response data
3. Configure proper formatters for different environments
4. Add performance monitoring

### Benefits

- Better log analysis
- Contextual logging
- Easier debugging
- Performance insights

## Dependency Changes

### Add

- `httpx>=0.24.0` - Modern async HTTP client
- `python-daemon>=3.0.0` - Daemon process management
- `langchain>=0.1.0` - LLM conversation management
- `structlog>=23.1.0` - Structured logging

### Remove

- None (keep existing dependencies but leverage them better)

## Implementation Approach

Phase 1: Infrastructure

- HTTP client refactoring
- Configuration with Pydantic
- Process management

Phase 2: Core Logic

- Session management with LangChain
- API error handling

Phase 3: User Experience

- Command registration improvements
- Structured logging

## Testing Strategy

1. Ensure existing tests pass with refactored code
2. Add tests for new functionality
3. Use the existing test structure but enhance where needed
4. Maintain or improve test coverage

## Documentation Updates

1. Update README.md with new dependencies and setup
2. Add architectural documentation explaining the refactored components
3. Update code comments to reflect new patterns
4. Create examples for extending the refactored system
