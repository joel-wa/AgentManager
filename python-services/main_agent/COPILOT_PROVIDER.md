# GitHub Copilot CLI Provider

This document describes how to use GitHub Copilot CLI as an AI provider for the main agent.

## Overview

The Copilot provider wraps the GitHub Copilot CLI (`gh copilot`) as an HTTP-accessible chat service, allowing you to use GitHub Copilot's capabilities through the AgentManager interface.

## Prerequisites

1. **GitHub Copilot CLI** - The standalone copilot command
   ```bash
   # Check if installed
   copilot --version
   ```
   
   If not installed, follow instructions at: https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line

2. **GitHub Authentication**
   The copilot CLI will prompt for authentication on first use.

## Configuration

### Using Copilot as the AI Provider

Set the `AI_PROVIDER` environment variable to `copilot`:

**Windows (PowerShell):**
```powershell
$env:AI_PROVIDER = "copilot"
```

**Windows (Command Prompt):**
```cmd
set AI_PROVIDER=copilot
```

**Linux/macOS:**
```bash
export AI_PROVIDER=copilot
```

**Or create a `.env` file** in the `python-services/main_agent/` directory:
```
AI_PROVIDER=copilot
```

### Using Ollama (Default)

If you want to switch back to Ollama, either unset the variable or set it to `ollama`:

```bash
export AI_PROVIDER=ollama
# or omit it entirely (ollama is the default)
```

## How It Works

### Architecture

```
┌─────────────────────────────────────────┐
│     Frontend / Rust Core               │
│     POST /agent/chat                    │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│   Main Agent (FastAPI on :8001)        │
│   ┌─────────────────────────────────┐   │
│   │   AI Provider Selection         │   │
│   │   ┌──────────┐  ┌────────────┐  │   │
│   │   │  Ollama  │  │  Copilot   │  │   │
│   │   │  Client  │  │  Client    │  │   │
│   │   └──────────┘  └────────────┘  │   │
│   └─────────────────────────────────┘   │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│   GitHub Copilot CLI (subprocess)       │
│   copilot -p "<prompt>"                 │
└─────────────────────────────────────────┘
```

### Request Flow

1. **Chat Request** arrives at `/agent/chat` endpoint
2. **Provider Selection**: Main agent checks `AI_PROVIDER` environment variable
3. **Copilot Client**: 
   - Converts chat messages to a Copilot-compatible prompt
   - Executes `copilot -p "<prompt>"` command (programmatic mode)
   - Parses the response and extracts any tool calls
4. **Tool Execution**: If Copilot suggests commands, they're mapped to tools:
   - `cat file.txt` → `read_file` tool
   - `ls directory/` → `list_directory` tool
   - Shell commands → `execute_command` tool
5. **Response**: Returns the Copilot response to the user

### Tool Call Mapping

The Copilot provider intelligently maps common shell commands to AgentManager tools:

| Copilot Suggestion | Mapped Tool | Example |
|-------------------|-------------|---------|
| `cat file.txt` | `read_file` | Reading file contents |
| `type file.txt` | `read_file` | Reading file contents (Windows) |
| `ls dir/` | `list_directory` | Listing directory contents |
| `dir folder/` | `list_directory` | Listing directory (Windows) |
| `grep "pattern" file` | `search` | Searching for content |
| Other commands | `execute_command` | Direct execution |

## Usage Examples

### Starting the Main Agent with Copilot

1. **Set the environment variable:**
   ```powershell
   $env:AI_PROVIDER = "copilot"
   ```

2. **Start the main agent:**
   ```bash
   cd python-services/main_agent
   python main.py
   ```

3. **Check health:**
   ```bash
   curl http://localhost:8001/health
   ```
   
   Should return:
   ```json
   {
     "status": "healthy",
     "model_available": true,
     "ollama_url": "github-copilot-cli"
   }
   ```

### Testing via API

```bash
# Send a chat message
curl -X POST http://localhost:8001/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all Python files in the current directory",
    "tools": ["list_directory", "execute_command"]
  }'
```

### Using with the Full Application

Once configured, the entire AgentManager system will use Copilot:

1. Set `AI_PROVIDER=copilot`
2. Start the application normally with `start-app.ps1`
3. Chat in the web interface as usual
4. Copilot will handle all AI interactions

## Benefits

✅ **GitHub Copilot's Intelligence**: Access to GitHub-trained models  
✅ **No Local GPU Required**: Runs entirely via cloud  
✅ **Persistent HTTP Service**: Copilot CLI wrapped as always-on service  
✅ **Tool Integration**: Automatic mapping of commands to AgentManager tools  
✅ **Seamless Switching**: Toggle between Ollama and Copilot via environment variable  

## Limitations

⚠️ **Requires GitHub Copilot Subscription**: Must have active Copilot access  
⚠️ **Internet Connection Required**: Copilot CLI requires internet  
⚠️ **Rate Limits**: Subject to GitHub Copilot API rate limits  
⚠️ **Command-Focused**: Copilot CLI is optimized for shell commands, not general chat  

## Troubleshooting

### "GitHub Copilot CLI not found"

**Solution:** Install the standalone GitHub Copilot CLI:
- Visit: https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line
- Ensure `copilot` command is in your PATH
- Test with: `copilot --version`

### "Not authenticated with GitHub"

**Solution:** Run copilot once to authenticate:
```bash
copilot -p "test prompt"
```
It will prompt you to authenticate on first use.

### "Error: Copilot returned error"

**Possible causes:**
- No active Copilot subscription
- Network connectivity issues
- GitHub API rate limiting

**Check Copilot status:**
```bash
copilot --version
copilot -p "test prompt"
```

### Health check shows "degraded"

The main agent is running but Copilot CLI is not available. Check:
1. Is `copilot` installed? (`copilot --version`)
2. Is `copilot` in your PATH?
3. Are you authenticated? Try running `copilot -p "hello"`

## Development Notes

### Files

- **`copilot_client.py`**: Main Copilot CLI wrapper
  - Manages subprocess communication with `gh copilot`
  - Parses responses and maps commands to tools
  - Implements same interface as `OllamaClient`

- **`main.py`**: Provider selection logic
  - Reads `AI_PROVIDER` environment variable
  - Initializes appropriate client (Ollama or Copilot)
  - Routes all AI requests through unified interface

### API Compatibility

The Copilot provider implements the same interface as the Ollama provider:
- `async def check_model() -> bool`
- `async def chat(messages, tools) -> Tuple[str, Optional[List]]`
- `async def complete(prompt) -> str`

This ensures seamless switching between providers without changing any other code.

## Future Enhancements

Potential improvements for the Copilot provider:

- [ ] Support for streaming responses
- [ ] Conversation history management within Copilot session
- [ ] Custom prompt templates optimized for Copilot
- [ ] Better error handling and retry logic
- [ ] Support for `gh copilot explain` mode
- [ ] Caching of frequent prompts
- [ ] Metrics and usage tracking

## License

This provider respects GitHub Copilot's terms of service and is designed for legitimate, authorized use of the GitHub Copilot CLI within its intended usage model.
