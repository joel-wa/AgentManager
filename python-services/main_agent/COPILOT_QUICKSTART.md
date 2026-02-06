# Quick Start: GitHub Copilot CLI Provider

Get up and running with GitHub Copilot as your AI provider in 5 minutes.

## Prerequisites Check

Run these commands to verify you have everything:

```powershell
# Check GitHub CLI
gh --version

# Check Copilot extension
gh extension list | Select-String copilot

# Check authentication
gh auth status

# Test Copilot
gh copilot suggest "list files in current directory"
```

If any of these fail, see the [installation section](#installation).

## Quick Start (Already Set Up)

If you already have GitHub Copilot CLI installed and authenticated:

### Windows (PowerShell)

```powershell
# 1. Set the provider
$env:AI_PROVIDER = "copilot"

# 2. Start the main agent
cd python-services\main_agent
python main.py

# 3. In another terminal, test it
curl http://localhost:8001/health
```

### Linux/macOS

```bash
# 1. Set the provider
export AI_PROVIDER=copilot

# 2. Start the main agent
cd python-services/main_agent
python main.py

# 3. In another terminal, test it
curl http://localhost:8001/health
```

That's it! The agent is now using GitHub Copilot CLI.

## Installation (If Needed)

### 1. Install GitHub CLI

**Windows:**
```powershell
winget install GitHub.cli
```

**macOS:**
```bash
brew install gh
```

**Linux (Debian/Ubuntu):**
```bash
type -p curl >/dev/null || sudo apt install curl -y
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y
```

### 2. Install Copilot Extension

```bash
gh extension install github/gh-copilot
```

### 3. Authenticate

```bash
gh auth login
```

Follow the prompts to authenticate with your GitHub account that has Copilot access.

### 4. Verify Installation

```bash
gh copilot suggest "echo hello world"
```

You should see Copilot's suggestion. If you get an error about not having access, you need a GitHub Copilot subscription.

## Using with Full Application

To use Copilot with the entire AgentManager system:

### Option 1: Environment Variable (Temporary)

**Windows (PowerShell):**
```powershell
$env:AI_PROVIDER = "copilot"
.\start-app.ps1
```

**Linux/macOS:**
```bash
AI_PROVIDER=copilot ./start-app.sh
```

### Option 2: Create .env File (Persistent)

Create `python-services/main_agent/.env`:
```
AI_PROVIDER=copilot
```

Then start normally:
```bash
./start-app.ps1  # Windows
./start-app.sh   # Linux/macOS
```

## Testing

### Test the Health Endpoint

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_available": true,
  "ollama_url": "github-copilot-cli"
}
```

### Test a Chat Request

```bash
curl -X POST http://localhost:8001/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What files are in the current directory?",
    "tools": ["list_directory"]
  }'
```

### Test via Web Interface

1. Start the full application (frontend + rust-core + python-services)
2. Open http://localhost:3000
3. Create or open a project
4. Send a message like "List all files"
5. Watch Copilot respond and potentially trigger tools

## Switching Between Providers

### Switch to Copilot

```powershell
$env:AI_PROVIDER = "copilot"
# Restart main agent
```

### Switch to Ollama (Default)

```powershell
$env:AI_PROVIDER = "ollama"
# Or just remove the variable:
Remove-Item Env:\AI_PROVIDER
# Restart main agent
```

No code changes needed—just restart the main agent service.

## Troubleshooting

### "Command 'gh' not found"

**Solution:** Install GitHub CLI (see [Installation](#installation))

### "Extension not found"

**Solution:** Install Copilot extension:
```bash
gh extension install github/gh-copilot
```

### "Not authenticated"

**Solution:** Login with gh:
```bash
gh auth login
```

### "You don't have access to GitHub Copilot"

**Solution:** You need a GitHub Copilot subscription. Get one at https://github.com/features/copilot

### Main agent shows "degraded" status

Check each prerequisite:
```bash
gh --version                          # Should show version
gh extension list                     # Should show gh-copilot
gh auth status                        # Should show logged in
gh copilot suggest "test"            # Should return suggestion
```

### Copilot seems slow

This is normal—Copilot CLI makes API calls to GitHub's servers, which can take a few seconds. It's slower than local Ollama but provides GitHub's model quality.

## What's Different from Ollama?

| Feature | Ollama | Copilot CLI |
|---------|--------|-------------|
| **Speed** | Fast (local GPU) | Slower (API calls) |
| **Internet** | Not required | Required |
| **Quality** | Depends on model | GitHub-trained models |
| **Cost** | Free (local compute) | Requires Copilot subscription |
| **Privacy** | Fully local | Sends to GitHub API |
| **Setup** | Install Ollama + models | Install gh CLI + authenticate |

## Next Steps

- Read [COPILOT_PROVIDER.md](./COPILOT_PROVIDER.md) for detailed architecture
- Explore tool call mapping behavior
- Try different prompts to see Copilot's shell command suggestions
- Contribute improvements to the provider!

## Getting Help

- Check the main [COPILOT_PROVIDER.md](./COPILOT_PROVIDER.md) documentation
- Review GitHub Copilot CLI docs: https://docs.github.com/en/copilot/github-copilot-in-the-cli
- Open an issue if you find bugs
