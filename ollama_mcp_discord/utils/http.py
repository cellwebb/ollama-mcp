"""Shared HTTP client module using HTTPX."""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client wrapper using HTTPX.

    This class provides a shared HTTPX client with connection pooling,
    logging, and consistent error handling.
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize the HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Default timeout in seconds
            headers: Default headers to send with all requests
        """
        self.base_url = base_url
        self.timeout = timeout
        self.headers = headers or {}
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=self.headers,
            follow_redirects=True,
        )

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Perform a GET request.

        Args:
            url: URL to request
            **kwargs: Additional arguments to pass to httpx

        Returns:
            JSON response as a dictionary

        Raises:
            HTTPError: If the request fails
        """
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Perform a POST request.

        Args:
            url: URL to request
            **kwargs: Additional arguments to pass to httpx

        Returns:
            JSON response as a dictionary

        Raises:
            HTTPError: If the request fails
        """
        return await self._request("POST", url, **kwargs)

    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Perform an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments to pass to httpx

        Returns:
            JSON response as a dictionary

        Raises:
            HTTPError: If the request fails
        """
        try:
            logger.debug(f"Making {method} request to {url}")
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()

            if response.headers.get("content-type") == "application/json":
                return response.json()

            # If not JSON, return a dict with the text
            return {"text": response.text}

        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error making request: {e}")
            raise

    async def close(self):
        """Close the client session."""
        if self.client:
            await self.client.aclose()

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.close()


# Factory function to create a client with specific configuration
def create_client(
    base_url: str = "",
    timeout: float = 30.0,
    headers: Optional[Dict[str, str]] = None,
) -> HTTPClient:
    """Create a new HTTP client.

    Args:
        base_url: Base URL for all requests
        timeout: Default timeout in seconds
        headers: Default headers to send with all requests

    Returns:
        Configured HTTP client
    """
    return HTTPClient(base_url=base_url, timeout=timeout, headers=headers)
