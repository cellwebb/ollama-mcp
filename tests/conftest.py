"""Common test fixtures and configurations."""

import uuid

import pytest

from ollama_mcp_discord.core.session import Session
from ollama_mcp_discord.mcp.client import MCPClient
from ollama_mcp_discord.ollama.client import OllamaClient


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")
    monkeypatch.setenv("MEMORY_SERVER_ENDPOINT", "http://localhost:3100")
    monkeypatch.setenv("FETCH_SERVER_ENDPOINT", "http://localhost:3101")
    monkeypatch.setenv("PUPPETEER_SERVER_ENDPOINT", "http://localhost:3102")
    monkeypatch.setenv("SEQUENTIAL_THINKING_SERVER_ENDPOINT", "http://localhost:3103")


@pytest.fixture
def sample_message():
    """Return a sample message dictionary."""
    return {
        "id": str(uuid.uuid4()),
        "content": "Test message",
        "author": {"id": "123456789", "username": "TestUser"},
    }


@pytest.fixture
def sample_conversation():
    """Return a sample conversation history."""
    return [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]


@pytest.fixture
def mock_ollama_client(mocker):
    """Create a mock OllamaClient with async methods."""
    mock_client = mocker.AsyncMock(spec=OllamaClient)

    # Simulate list_models method
    mock_client.list_models.return_value = [
        {"name": "llama3", "modified_at": "2023-06-01T12:00:00Z"},
        {"name": "mistral", "modified_at": "2023-05-30T10:30:00Z"},
    ]

    # Simulate generate method
    mock_client.generate.return_value = "Test response"

    # Add the model property for the set_model tests
    mock_client.model = "llama3"

    return mock_client


@pytest.fixture
def mock_mcp_client(mocker):
    """Create a mock MCPClient with async methods."""
    mock_client = mocker.AsyncMock(spec=MCPClient)

    # Simulate memory client methods
    mock_client.create_memory_entity.return_value = "memory-uuid"
    mock_client.fetch_url.return_value = {"content": "Test URL content"}
    mock_client.navigate.return_value = {"status": "success"}
    mock_client.screenshot.return_value = {"screenshot_path": "/path/to/screenshot"}
    mock_client.think.return_value = {"thought": "Test thinking result"}

    return mock_client


@pytest.fixture
async def session(mock_ollama_client, mock_mcp_client):
    """Create a Session instance with mocked clients."""
    return Session(user_id="test-user", ollama_client=mock_ollama_client, mcp_client=mock_mcp_client)
