"""Common test fixtures and configurations."""

import os
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with mock.patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "mock-token",
            "OLLAMA_HOST": "http://localhost:11434",
            "DEFAULT_MODEL": "llama3",
            "MEMORY_ENDPOINT": "http://localhost:3000",
            "FETCH_ENDPOINT": "http://localhost:3001",
            "PUPPETEER_ENDPOINT": "http://localhost:3002",
            "SEQUENTIAL_THINKING_ENDPOINT": "http://localhost:3003",
        },
    ):
        yield


@pytest.fixture
def sample_message():
    """Return a sample message dictionary for testing."""
    return {"role": "user", "content": "Hello, this is a test message"}


@pytest.fixture
def sample_conversation():
    """Return a sample conversation history for testing."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
        {"role": "user", "content": "Tell me about Ollama"},
        {
            "role": "assistant",
            "content": "Ollama is an open-source platform for running large language models locally.",
        },
    ]
