# MCP Server Documentation

This document provides detailed information about the Model Context Protocol (MCP) servers used in this project, their configuration, and usage.

## Overview

The Model Context Protocol (MCP) is an open standard that enables AI systems to connect and interact with external tools, data sources, and services. MCP servers act as connectors that provide AI agents with access to resources like databases, APIs, and filesystems through a standardized interface.

Our project implements a modular MCP server architecture, allowing different specialized servers to handle specific functionalities:

## Supported MCP Servers

### Memory MCP Server

The Memory MCP Server stores and retrieves information about entities and conversations.

- **Default endpoint:** `http://localhost:3100`
- **Environment variable:** `MEMORY_SERVER_ENDPOINT`
- **Key functionalities:**
  - Create and update entities with observations
  - Retrieve entity information
  - Manage conversation memories

### Fetch MCP Server

The Fetch MCP Server retrieves content from URLs, allowing the AI to access information from the internet.

- **Default endpoint:** `http://localhost:3101`
- **Environment variable:** `FETCH_SERVER_ENDPOINT`
- **Key functionalities:**
  - Fetch content from web pages
  - Extract information from web content
  - Provide up-to-date information to the AI

### Puppeteer MCP Server

The Puppeteer MCP Server enables browser automation, allowing more complex web interactions.

- **Default endpoint:** `http://localhost:3102`
- **Environment variable:** `PUPPETEER_SERVER_ENDPOINT`
- **Key functionalities:**
  - Navigate to web pages
  - Screenshot web content
  - Perform actions like clicking buttons and filling forms

### Sequential Thinking MCP Server

The Sequential Thinking MCP Server facilitates multi-step reasoning processes.

- **Default endpoint:** `http://localhost:3103`
- **Environment variable:** `SEQUENTIAL_THINKING_SERVER_ENDPOINT`
- **Key functionalities:**
  - Break down complex problems into steps
  - Track reasoning across multiple thoughts
  - Provide more structured problem-solving capabilities

## Configuration

MCP servers can be configured using:

1. Environment variables
2. Configuration file (`mcp.json`)

### Environment Variables

The following environment variables can be used to configure MCP server endpoints:

```bash
MEMORY_SERVER_ENDPOINT=http://localhost:3100
FETCH_SERVER_ENDPOINT=http://localhost:3101
PUPPETEER_SERVER_ENDPOINT=http://localhost:3102
SEQUENTIAL_THINKING_SERVER_ENDPOINT=http://localhost:3103
MCP_CONFIG_PATH=path/to/mcp.json
```

### Configuration File

The `mcp.json` file defines how MCP servers are started and configured:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/path/to/memory-file.json"
      }
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "mcp-puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "PUPPETEER_LAUNCH_OPTIONS": "{ \"headless\": true}",
        "ALLOW_DANGEROUS": "false"
      }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

Each server configuration includes:

- `command`: The command to run the server
- `args`: Arguments for the command
- `env`: Environment variables for the server process

## Security Best Practices

When working with MCP servers, follow these security best practices:

1. **Never hardcode API keys or sensitive information**

   - Use environment variables for all sensitive data
   - Store credentials securely using environment variables or a secure credential manager

2. **Limit permissions**

   - Set appropriate access controls for MCP servers
   - For Puppeteer server, avoid enabling `ALLOW_DANGEROUS` unless necessary

3. **Validate input**
   - Always validate and sanitize input before passing it to MCP servers
   - Implement rate limiting to prevent abuse

## Adding New MCP Servers

To add a new MCP server:

1. Create a new server class in `ollama_mcp_discord/mcp/servers/`
2. Inherit from `BaseMCPServer` and implement required methods
3. Add the server to the `MCPClient` class
4. Update configuration handling in `core/config.py`
5. Add documentation for the new server

Example implementation:

```python
class CustomMCPServer(BaseMCPServer):
    """Custom MCP server implementation."""

    async def custom_method(self, param1: str) -> Dict[str, Any]:
        """Implement custom functionality.

        Args:
            param1: Description of parameter

        Returns:
            Response from the server
        """
        payload = {"param1": param1}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/custom_endpoint", json=payload
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Error in custom method: {e}")
            raise
```

## Troubleshooting

Common issues and their solutions:

### MCP Server Not Starting

If an MCP server fails to start:

1. Check that the command is installed and available in your PATH
2. Verify the configuration in `mcp.json` is correct
3. Check environment variables required by the server
4. Look for error messages in the logs

### Connection Errors

If the application cannot connect to an MCP server:

1. Verify the server is running using `netstat -an | grep <port>`
2. Check the endpoint configuration in environment variables
3. Ensure firewall settings allow connections to the specified port
4. Verify network connectivity if using remote servers

## Resources

- [Model Context Protocol (MCP) Documentation](https://github.com/awslabs/mcp)
- [MCP Server Implementation Guide](https://awslabs.github.io/mcp/)
- [MCP Servers: A Comprehensive Guide](https://medium.com/data-and-beyond/mcp-servers-a-comprehensive-guide-another-way-to-explain-67c2fa58f650)
