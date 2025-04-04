"""Tests for the MCP client."""

from unittest import mock

import pytest
from pytest_mock import MockerFixture

from ollama_mcp_discord.mcp.client import MCPClient


class TestMCPClient:
    """Behavior tests for the MCP client."""

    @pytest.fixture
    def client(self):
        """Create a test MCP client instance."""
        return MCPClient()

    @pytest.fixture
    def mock_memory_client(self, mocker: MockerFixture):
        """Create a mock MCP Memory client."""
        mock_client = mocker.MagicMock()
        mock_client.create_entities = mocker.AsyncMock()
        mock_client.create_entities.return_value = {"success": True}
        return mock_client

    @pytest.fixture
    def mock_fetch_client(self, mocker: MockerFixture):
        """Create a mock MCP Fetch client."""
        mock_client = mocker.MagicMock()
        mock_client.fetch = mocker.AsyncMock()
        mock_client.fetch.return_value = {"content": "Mock fetch content"}
        return mock_client

    @pytest.fixture
    def mock_puppeteer_client(self, mocker: MockerFixture):
        """Create a mock MCP Puppeteer client."""
        mock_client = mocker.MagicMock()
        mock_client.navigate = mocker.AsyncMock()
        mock_client.navigate.return_value = {"success": True}
        mock_client.screenshot = mocker.AsyncMock()
        mock_client.screenshot.return_value = {"imageUrl": "mock-screenshot.png"}
        return mock_client

    @pytest.fixture
    def mock_thinking_client(self, mocker: MockerFixture):
        """Create a mock MCP Sequential Thinking client."""
        mock_client = mocker.MagicMock()
        mock_client.sequentialthinking = mocker.AsyncMock()
        mock_client.sequentialthinking.return_value = {"thought": "Mock thought"}
        return mock_client

    @pytest.mark.asyncio
    async def test_create_memory_entity_creates_entity_successfully(
        self, client, mocker: MockerFixture, mock_memory_client
    ):
        """
        Given entity information
        When creating a memory entity
        Then it should be created successfully through the MCP memory client
        """
        # Given
        mocker.patch.object(client, "_memory_client", mock_memory_client)

        entity_name = "test-entity"
        entity_type = "UserMemory"
        observations = ["Test observation"]

        # When
        result = await client.create_memory_entity(name=entity_name, entity_type=entity_type, observations=observations)

        # Then
        mock_memory_client.create_entities.assert_called_once()
        call_args = mock_memory_client.create_entities.call_args[0][0]
        assert call_args["entities"][0]["name"] == entity_name
        assert call_args["entities"][0]["entityType"] == entity_type
        assert call_args["entities"][0]["observations"] == observations
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_fetch_url_retrieves_content_through_fetch_client(
        self, client, mocker: MockerFixture, mock_fetch_client
    ):
        """
        Given a URL to fetch
        When fetching the URL
        Then content should be retrieved through the MCP fetch client
        """
        # Given
        mocker.patch.object(client, "_fetch_client", mock_fetch_client)
        url = "https://example.com"

        # When
        result = await client.fetch_url(url)

        # Then
        mock_fetch_client.fetch.assert_called_once()
        assert mock_fetch_client.fetch.call_args[0][0]["url"] == url
        assert result == {"content": "Mock fetch content"}

    @pytest.mark.asyncio
    async def test_navigate_browser_navigates_through_puppeteer_client(
        self, client, mocker: MockerFixture, mock_puppeteer_client
    ):
        """
        Given a URL to navigate to
        When navigating the browser
        Then it should navigate through the MCP puppeteer client
        """
        # Given
        mocker.patch.object(client, "_puppeteer_client", mock_puppeteer_client)
        url = "https://example.com"

        # When
        result = await client.navigate_browser(url)

        # Then
        mock_puppeteer_client.navigate.assert_called_once()
        assert mock_puppeteer_client.navigate.call_args[0][0]["url"] == url
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_take_screenshot_captures_through_puppeteer_client(
        self, client, mocker: MockerFixture, mock_puppeteer_client
    ):
        """
        Given screenshot parameters
        When taking a screenshot
        Then it should capture through the MCP puppeteer client
        """
        # Given
        mocker.patch.object(client, "_puppeteer_client", mock_puppeteer_client)
        name = "test-screenshot"

        # When
        result = await client.take_screenshot(name)

        # Then
        mock_puppeteer_client.screenshot.assert_called_once()
        assert mock_puppeteer_client.screenshot.call_args[0][0]["name"] == name
        assert result == {"imageUrl": "mock-screenshot.png"}

    @pytest.mark.asyncio
    async def test_sequential_thinking_processes_through_thinking_client(
        self, client, mocker: MockerFixture, mock_thinking_client
    ):
        """
        Given thinking parameters
        When performing sequential thinking
        Then it should process through the MCP sequential thinking client
        """
        # Given
        mocker.patch.object(client, "_thinking_client", mock_thinking_client)
        thought = "Initial thought"

        # When
        result = await client.sequential_thinking(thought)

        # Then
        mock_thinking_client.sequentialthinking.assert_called_once()
        assert mock_thinking_client.sequentialthinking.call_args[0][0]["thought"] == thought
        assert result == {"thought": "Mock thought"}

    @pytest.mark.asyncio
    async def test_create_memory_entity_server_error(self, client, mocker: MockerFixture, mock_memory_client):
        """
        Given entity information
        When creating a memory entity and the server returns an error
        Then the error should be handled gracefully
        """
        # Given
        mock_memory_client.create_entities = mocker.AsyncMock()
        mock_memory_client.create_entities.side_effect = Exception("Server error")
        mocker.patch.object(client, "_memory_client", mock_memory_client)

        entity_name = "test-entity"
        entity_type = "UserMemory"
        observations = ["Test observation"]

        # When/Then
        with pytest.raises(Exception) as excinfo:
            await client.create_memory_entity(name=entity_name, entity_type=entity_type, observations=observations)

        assert "Server error" in str(excinfo.value)
        mock_memory_client.create_entities.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_url_with_invalid_url(self, client, mocker: MockerFixture, mock_fetch_client):
        """
        Given an invalid URL to fetch
        When fetching the URL
        Then it should handle the invalid URL gracefully
        """
        # Given
        mocker.patch.object(client, "_fetch_client", mock_fetch_client)
        invalid_url = "not-a-valid-url"

        # Make fetch function return an error for invalid URL
        mock_fetch_client.fetch = mocker.AsyncMock()
        mock_fetch_client.fetch.side_effect = ValueError("Invalid URL format")

        # When/Then
        with pytest.raises(ValueError) as excinfo:
            await client.fetch_url(invalid_url)

        assert "Invalid URL format" in str(excinfo.value)
        mock_fetch_client.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_url_with_empty_url(self, client, mocker: MockerFixture, mock_fetch_client):
        """
        Given an empty URL to fetch
        When fetching the URL
        Then it should raise an appropriate validation error
        """
        # Given
        mocker.patch.object(client, "_fetch_client", mock_fetch_client)
        empty_url = ""

        # When/Then
        with pytest.raises(ValueError) as excinfo:
            await client.fetch_url(empty_url)

        assert "URL cannot be empty" in str(excinfo.value) or "Invalid URL" in str(excinfo.value)
        # Fetch client should not be called if validation catches the empty URL
        mock_fetch_client.fetch.assert_not_called()
