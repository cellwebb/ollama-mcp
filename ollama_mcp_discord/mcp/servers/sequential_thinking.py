"""Sequential Thinking MCP server implementation."""

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from ollama_mcp_discord.mcp.servers.base import BaseMCPServer

logger = logging.getLogger(__name__)


class SequentialThinkingMCPServer(BaseMCPServer):
    """Sequential Thinking MCP server for multi-step reasoning."""

    async def think(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        next_thought_needed: bool = True,
        is_revision: bool = False,
        revises_thought: Optional[int] = None,
        branch_from_thought: Optional[int] = None,
        branch_id: Optional[str] = None,
        needs_more_thoughts: bool = False,
    ) -> Dict[str, Any]:
        """Execute a sequential thinking step.

        Args:
            thought: Current thinking step
            thought_number: Current step number
            total_thoughts: Total expected steps
            next_thought_needed: Whether another step is needed
            is_revision: Whether this thought revises a previous one
            revises_thought: Which thought is being revised (if any)
            branch_from_thought: Which thought to branch from (if any)
            branch_id: Branch identifier (if any)
            needs_more_thoughts: Whether more thoughts are needed

        Returns:
            Response from the sequential thinking server
        """
        payload = {
            "thought": thought,
            "thoughtNumber": thought_number,
            "totalThoughts": total_thoughts,
            "nextThoughtNeeded": next_thought_needed,
        }

        # Add optional parameters if provided
        if is_revision:
            payload["isRevision"] = is_revision

        if revises_thought:
            payload["revisesThought"] = revises_thought

        if branch_from_thought:
            payload["branchFromThought"] = branch_from_thought

        if branch_id:
            payload["branchId"] = branch_id

        if needs_more_thoughts:
            payload["needsMoreThoughts"] = needs_more_thoughts

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/mcp_sequential_thinking_sequentialthinking", json=payload
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error in sequential thinking: {e}")
            raise

    async def start_thinking(self, initial_thought: str, estimated_steps: int) -> Dict[str, Any]:
        """Start a sequential thinking process.

        Args:
            initial_thought: First thinking step
            estimated_steps: Estimated number of steps

        Returns:
            Response from the sequential thinking server
        """
        return await self.think(
            thought=initial_thought,
            thought_number=1,
            total_thoughts=estimated_steps,
            next_thought_needed=True,
        )

    async def conclude_thinking(
        self, final_thought: str, thought_number: int, total_thoughts: int
    ) -> Dict[str, Any]:
        """Conclude a sequential thinking process.

        Args:
            final_thought: Final thinking step
            thought_number: Current step number
            total_thoughts: Total steps taken

        Returns:
            Response from the sequential thinking server
        """
        return await self.think(
            thought=final_thought,
            thought_number=thought_number,
            total_thoughts=total_thoughts,
            next_thought_needed=False,
        )
