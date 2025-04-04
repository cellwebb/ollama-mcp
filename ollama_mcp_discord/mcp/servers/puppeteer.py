"""Puppeteer MCP server implementation."""

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from ollama_mcp_discord.mcp.servers.base import BaseMCPServer

logger = logging.getLogger(__name__)


class PuppeteerMCPServer(BaseMCPServer):
    """Puppeteer MCP server for browser automation."""

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL using Puppeteer.

        Args:
            url: URL to navigate to

        Returns:
            Response from the Puppeteer server
        """
        payload = {"url": url}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/mcp_puppeteer_navigate", json=payload
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error navigating to URL: {e}")
            raise

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click on an element using Puppeteer.

        Args:
            selector: CSS selector for the element to click

        Returns:
            Response from the Puppeteer server
        """
        payload = {"selector": selector}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/mcp_puppeteer_click", json=payload
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            raise

    async def type(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into an element using Puppeteer.

        Args:
            selector: CSS selector for the element to type into
            text: Text to type

        Returns:
            Response from the Puppeteer server
        """
        payload = {"selector": selector, "text": text}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/mcp_puppeteer_type", json=payload
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            raise

    async def screenshot(self, selector: Optional[str] = None, full_page: bool = False) -> str:
        """Take a screenshot using Puppeteer.

        Args:
            selector: Optional CSS selector to screenshot a specific element
            full_page: Whether to take a full page screenshot

        Returns:
            Base64-encoded screenshot image
        """
        payload = {"selector": selector, "fullPage": full_page}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/mcp_puppeteer_screenshot", json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result.get("screenshot", "")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            raise
