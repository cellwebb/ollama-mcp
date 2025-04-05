# Ollama MCP Discord Bot

A Discord bot powered by Ollama and MCP servers, providing AI-powered interactions.

## Prerequisites

- Python 3.8+
- `uv` package manager

## Installation

1. **Install uv**:

   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File ./install.ps1
   ```

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yourusername/ollama-mcp-discord.git
   cd ollama-mcp-discord
   ```

1. **Create and Activate Virtual Environment**:

   ```bash
   uv venv
   source .venv/bin/activate  # macOS/Linux
   # OR
   .venv\Scripts\activate     # Windows
   ```

1. **Install Project Dependencies**:

   ```bash
   uv pip install .
   ```

1. **Install Development Dependencies** (optional):

   ```bash
   uv pip install .[dev]
   ```

## Configuration

1. **Copy Environment Template**:

   ```bash
   cp .env.example .env
   ```

1. **Edit `.env` and Add Your Discord Token**:

   ```bash
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

## Running the Bot

```bash
python -m ollama_mcp_discord
```

## Development

### Running Tests

```bash
uv pip install .[dev]
make test
```

### Code Formatting

```bash
black .
isort .
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Features

- Chat with AI models using Discord
- Select different AI models
- Create and manage memories
- Set custom system messages

## Commands

### Basic Commands

- `!chat <message>` - Chat with the AI model
- `!model <model_name>` - Select a different AI model
- `!remember <content>` - Create a new memory
- `!system_message <message>` - Set a custom system message for the AI
- `!help` - Show available commands

## Quick Start

1. Clone this repository
2. Install dependencies: `uv pip install -r requirements.txt`
3. Configure environment variables in `.env`
4. Start the bot: `python -m ollama_mcp_discord`

## Configuration

Create a `.env` file with the following variables:

```bash
DISCORD_TOKEN=your_discord_bot_token
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=llama3
```

## MCP Server Configuration

The Ollama-MCP Discord bot uses Model Context Protocol (MCP) servers to extend its capabilities. These servers provide specialized services like memory management, web fetching, browser automation, and sequential reasoning.

### Server Types

1. **Memory Server**: Stores and retrieves contextual information

   - Default Endpoint: `http://localhost:3100`
   - Package: `@modelcontextprotocol/server-memory`

2. **Fetch Server**: Retrieves web content

   - Default Endpoint: `http://localhost:3101`
   - Package: `mcp-server-fetch`

3. **Puppeteer Server**: Enables browser automation

   - Default Endpoint: `http://localhost:3102`
   - Package: `@modelcontextprotocol/server-puppeteer`

4. **Sequential Thinking Server**: Supports multi-step reasoning
   - Default Endpoint: `http://localhost:3103`
   - Package: `@modelcontextprotocol/server-sequential-thinking`

### Configuration File

Create a `mcp.json` file in the project root to configure MCP servers:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/path/to/memory-storage.json"
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

### Manual Server Management

If automatic server startup fails, you can manually start servers:

```bash
# Memory Server
npx -y @modelcontextprotocol/server-memory

# Fetch Server
uvx mcp-server-fetch

# Puppeteer Server
npx -y @modelcontextprotocol/server-puppeteer

# Sequential Thinking Server
npx -y @modelcontextprotocol/server-sequential-thinking
```

### Troubleshooting MCP Servers

#### Common Issues

1. **Server Not Starting**

   - Ensure all required packages are installed
   - Check that the specified command exists
   - Verify network ports are available

2. **Connection Errors**
   - Confirm servers are running on expected ports
   - Check firewall settings
   - Ensure no other applications are using the ports

#### Debugging Steps

1. Verify server installation:

   ```bash
   npx -y @modelcontextprotocol/server-memory --version
   ```

2. Check port availability:

   ```bash
   # macOS/Linux
   lsof -i :3100  # Replace with specific port

   # Windows
   netstat -ano | findstr :3100
   ```

3. Run servers with verbose logging:
   ```bash
   # Add verbose flag or environment variables for debugging
   DEBUG=* npx -y @modelcontextprotocol/server-memory
   ```

### Environment Variables

- `MEMORY_SERVER_ENDPOINT`: Custom memory server URL
- `FETCH_SERVER_ENDPOINT`: Custom fetch server URL
- `PUPPETEER_SERVER_ENDPOINT`: Custom puppeteer server URL
- `SEQUENTIAL_THINKING_SERVER_ENDPOINT`: Custom sequential thinking server URL
- `MCP_CONFIG_PATH`: Path to MCP configuration file (default: `mcp.json`)

### Security Considerations

- Use `ALLOW_DANGEROUS=false` for Puppeteer server
- Set specific memory file paths
- Limit server exposure to trusted networks

## Usage

The bot provides several ways to interact:

### Text Commands

- `!chat <message>` - Have a conversation with the AI model

  ```text
  !chat What is the capital of France?
  !chat Can you help me with Python programming?
  ```

- `!model <model_name>` - Switch to a different Ollama model

  ```text
  !model llama3
  !model mistral
  ```

- `!remember <content>` - Store information in the AI's memory

  ```text
  !remember My favorite color is blue
  !remember Python is a programming language
  ```

  ```text

  ```

  ```text

  ```

- `!help` - Display help information about all available commands

### Automatic Responses

- The bot only responds to whole words, not parts of words

### Tips

1. The bot maintains conversation history for context
2. You can use any Ollama model that's installed on your server
3. The bot has access to several tools through MCP servers:
   - Memory: Store and retrieve information
   - Fetch: Get information from the web
   - Puppeteer: Control a browser
   - Sequential Thinking: Break down complex problems

### Example Conversation

```text
User: !model llama3
Bot: Model set to llama3

User: !chat Tell me about Python
Bot: [Detailed response about Python]

User: hello
Bot: Hello there! How can I help you today?

User: !remember Python is a high-level programming language
Bot: I'll remember that! Memory created with ID: [memory_id]
```

## Development

Check the ROADMAP.md file for implementation status and upcoming features.

## System Message Management

### Setting System Message

You can set the system message for the model in two ways:

1. Using a Slash Command:

   ```
   /set_system_message Your custom system message here
   ```

2. Programmatically:

   ```python
   from system_message import set_system_message

   set_system_message("Your custom system message here")
   ```

### Retrieving System Message

```python
from system_message import get_system_message

current_message = get_system_message()
print(current_message)
```

### Clearing System Message

```python
from system_message import clear_system_message

clear_system_message()
```

The system message is stored in `~/.mcp_system_message.json` and persists between sessions.
