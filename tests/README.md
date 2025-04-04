# Tests for Ollama-MCP Discord Bot

This directory contains tests for the Ollama-MCP Discord bot. The tests are behavior-driven and designed to verify that the various components of the application work as expected.

## Test Structure

The tests are organized by component:

- `test_ollama_client.py`: Tests for the Ollama client
- `test_mcp_client.py`: Tests for the MCP client
- `test_session.py`: Tests for the Session class
- `test_discord_bot.py`: Tests for the Discord bot

## Testing Approach

We follow a behavior-driven approach to testing, where each test:

1. **Sets up the necessary context** ("Given...")
2. **Performs an action** ("When...")
3. **Verifies the expected outcomes** ("Then...")

## Running Tests

To run the tests, use the make commands from the root directory:

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov
```

## Writing New Tests

When writing new tests, follow these guidelines:

1. Use the existing test structure as a template
2. Write tests that focus on behavior, not implementation details
3. Use descriptive test names that explain what's being tested
4. Use fixtures to set up common test data and mocks
5. Use the Given-When-Then pattern in test docstrings

Example:

```python
@pytest.mark.asyncio
async def test_some_feature_behaves_as_expected(self):
    """
    Given some context or setup
    When an action is performed
    Then the expected outcome should happen
    """
    # Given
    # setup code...

    # When
    # action code...

    # Then
    # assertions...
```
