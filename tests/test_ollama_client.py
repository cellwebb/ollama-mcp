"""Tests for the OllamaClient class."""

import json
from unittest import mock

import pytest

from ollama_mcp_discord.ollama.client import OllamaClient


class TestOllamaClient:
    """Behavior tests for the OllamaClient class."""

    @pytest.fixture
    def client(self):
        """Create a test OllamaClient instance."""
        return OllamaClient(host="http://test.ollama:11434", model="test-model")

    @pytest.mark.asyncio
    async def test_list_models_returns_available_models(self, client):
        """When listing models, it should return models from the Ollama API."""
        # Given
        mock_response = mock.AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3", "modified_at": "2023-06-01T12:00:00Z"},
                {"name": "mistral", "modified_at": "2023-05-30T10:30:00Z"},
            ]
        }

        with mock.patch("aiohttp.ClientSession.get", return_value=mock_response):
            # When
            result = await client.list_models()

            # Then
            assert len(result) == 2
            assert result[0]["name"] == "llama3"
            assert result[1]["name"] == "mistral"

    @pytest.mark.asyncio
    async def test_generate_returns_model_response(self, client):
        """When generating text, it should return the model's response."""
        # Given
        mock_response = mock.AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "model": "test-model",
            "response": "This is a test response",
            "done": True,
        }

        with mock.patch("aiohttp.ClientSession.post", return_value=mock_response):
            # When
            result = await client.generate(
                prompt="Test prompt",
                system="You are a test assistant",
                context=[],
            )

            # Then
            assert result == "This is a test response"

    @pytest.mark.asyncio
    async def test_generate_with_context_sends_correct_payload(self, client):
        """When generating with context, it should include context in the payload."""
        # Given
        mock_post = mock.AsyncMock()
        mock_post.return_value.__aenter__.return_value.status = 200
        mock_post.return_value.__aenter__.return_value.json.return_value = {
            "model": "test-model",
            "response": "Response with context",
            "done": True,
        }

        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
        ]

        with mock.patch("aiohttp.ClientSession.post", mock_post):
            # When
            await client.generate(
                prompt="New message",
                system="You are a test assistant",
                context=context,
            )

            # Then
            # Extract the payload from the call
            call_args = mock_post.call_args
            assert call_args is not None

            # Verify the payload contains the context
            payload = json.loads(call_args[1]["json"])
            assert payload["model"] == "test-model"
            assert payload["prompt"] == "New message"
            assert payload["system"] == "You are a test assistant"
            assert payload["context"] == context

    @pytest.mark.asyncio
    async def test_generate_handles_error_response(self, client):
        """When Ollama API returns an error, it should raise an exception."""
        # Given
        mock_response = mock.AsyncMock()
        mock_response.status = 400
        mock_response.json.return_value = {"error": "Invalid model"}
        mock_response.text.return_value = "Invalid model"

        with mock.patch("aiohttp.ClientSession.post", return_value=mock_response), pytest.raises(
            ValueError, match="Error from Ollama API: Invalid model"
        ):
            # When/Then
            await client.generate(prompt="Test prompt")
