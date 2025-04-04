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
        mock_client.create_memory_entity = mocker.AsyncMock()
        mock_client.create_memory_entity.return_value = {"success": True}
        return mock_client

    @pytest.fixture
    def mock_fetch_client(self, mocker: MockerFixture):
        """Create a mock MCP Fetch client."""
        mock_client = mocker.MagicMock()
        mock_client.fetch_url = mocker.AsyncMock()
        mock_client.fetch_url.return_value = "Mock fetch content"
        return mock_client

    @pytest.fixture
    def mock_puppeteer_client(self, mocker: MockerFixture):
        """Create a mock MCP Puppeteer client."""
        mock_client = mocker.MagicMock()
        mock_client.navigate = mocker.AsyncMock()
        mock_client.navigate.return_value = {"success": True}
        mock_client.screenshot = mocker.AsyncMock()
        mock_client.screenshot.return_value = "mock-screenshot.png"
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
        mocker.patch.object(client, "memory_server", mock_memory_client)

        entity_name = "test-entity"
        entity_type = "UserMemory"
        observations = ["Test observation"]

        # When
        result = await client.create_memory_entity(name=entity_name, entity_type=entity_type, observations=observations)

        # Then
        mock_memory_client.create_memory_entity.assert_called_once_with(entity_name, entity_type, observations)
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
        mocker.patch.object(client, "fetch_server", mock_fetch_client)
        url = "https://example.com"
        max_length = 5000

        # When
        result = await client.fetch_url(url)

        # Then
        mock_fetch_client.fetch_url.assert_called_once_with(url, max_length)
        assert result == "Mock fetch content"

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
        mocker.patch.object(client, "puppeteer_server", mock_puppeteer_client)
        url = "https://example.com"

        # When
        result = await client.navigate(url)

        # Then
        mock_puppeteer_client.navigate.assert_called_once_with(url)
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
        mocker.patch.object(client, "puppeteer_server", mock_puppeteer_client)
        selector = "#test-element"
        full_page = False

        # When
        result = await client.screenshot(selector, full_page)

        # Then
        mock_puppeteer_client.screenshot.assert_called_once_with(selector, full_page)
        assert result == "mock-screenshot.png"

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
        mocker.patch.object(client, "sequential_thinking_server", mock_thinking_client)
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
        mock_memory_client.create_memory_entity = mocker.AsyncMock()
        mock_memory_client.create_memory_entity.side_effect = Exception("Server error")
        mocker.patch.object(client, "memory_server", mock_memory_client)

        entity_name = "test-entity"
        entity_type = "UserMemory"
        observations = ["Test observation"]

        # When/Then
        with pytest.raises(Exception) as excinfo:
            await client.create_memory_entity(name=entity_name, entity_type=entity_type, observations=observations)

        assert "Server error" in str(excinfo.value)
        mock_memory_client.create_memory_entity.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_url_with_invalid_url(self, client, mocker: MockerFixture, mock_fetch_client):
        """
        Given an invalid URL to fetch
        When fetching the URL
        Then it should handle the invalid URL gracefully
        """
        # Given
        mocker.patch.object(client, "fetch_server", mock_fetch_client)
        invalid_url = "not-a-valid-url"

        # Make fetch function return an error for invalid URL
        mock_fetch_client.fetch_url = mocker.AsyncMock()
        mock_fetch_client.fetch_url.side_effect = ValueError("Invalid URL format")

        # When/Then
        with pytest.raises(ValueError) as excinfo:
            await client.fetch_url(invalid_url)

        assert "Invalid URL format" in str(excinfo.value)
        mock_fetch_client.fetch_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_url_with_empty_url(self, client, mocker: MockerFixture, mock_fetch_client):
        """
        Given an empty URL to fetch
        When fetching the URL
        Then it should raise an appropriate validation error
        """
        # Given
        mocker.patch.object(client, "fetch_server", mock_fetch_client)
        empty_url = ""

        # Add input validation to the fetch_url method
        # When/Then
        with pytest.raises(ValueError) as excinfo:
            await client.fetch_url(empty_url)

        assert "URL cannot be empty" in str(excinfo.value) or "Invalid URL" in str(excinfo.value)
        # Fetch client should not be called if validation catches the empty URL
        mock_fetch_client.fetch_url.assert_not_called()
