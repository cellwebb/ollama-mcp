# Ollama-MCP Discord Bot

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

- Connect to local Ollama models
- Access MCP capabilities (memory, fetch, puppeteer, sequential thinking)
- User-friendly Discord bot interface with text commands
- Respond to specific trigger words in normal messages
- Multi-user conversation support
- Configurable model selection

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

The Ollama-MCP Discord bot can interact with various MCP servers. To configure these servers, create a `mcp.json` file in the project root with the following structure:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/Users/cell/.windsurf-memory.json"
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
        "PUPPETEER_LAUNCH_OPTIONS": "{ \"headless\": false}",
        "ALLOW_DANGEROUS": "true"
      }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

### Starting the Bot

To start the bot, run the following command:

```bash
python -m ollama_mcp_discord
```

The bot will automatically start the configured MCP servers.

### Environment Variables

- `DISCORD_TOKEN`: Required for the Discord bot to authenticate.
- `MCP_CONFIG_PATH`: Optional path to the MCP configuration file (default: `mcp.json`).

## Usage

Once the bot is running, you can interact with it in Discord using text commands:

```text
!chat What's the weather like today?
!model llama3
!remember Create a new memory item
!trigger add keyword Your custom response
!trigger remove keyword
!triggers
!help
```

The bot will also automatically respond to certain words in normal conversation:

- When someone says "hello" in chat, the bot will respond
- You can add or remove trigger words with the `!trigger` command

## Development

Check the ROADMAP.md file for implementation status and upcoming features.
