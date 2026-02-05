# Agent Workspace

A modern, minimalist AI agent workspace system that gives local Ollama models persistent memory and file management capabilities.

## Architecture

The system consists of three main components:

1. **Frontend (React/TypeScript)** - Modern chat-first interface
2. **Rust Core Engine** - WebSocket server, file system management, coordination
3. **Python Services** - AI agents and embedding generation

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React + Tailwind)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   Chat Interface   │   File Browser   │   Timeline       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │ WebSocket / REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Rust Core Engine (:8000)                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │ WebSocket  │  │   File     │  │  Project   │  │  Session  │ │
│  │  Server    │  │  Manager   │  │  Manager   │  │  Logger   │ │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Main Agent     │  │  Maintenance    │  │   Embedding     │
│   (:8001)       │  │   Agent (:8002) │  │  Service (:8003)│
│  Local Gemma    │  │  Cloud AI       │  │  Sentence-Trans │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Features

- **Chat-First Interface**: Clean, minimal chat with your local AI agent
- **Persistent Memory**: Files and notes are stored in organized workspaces
- **Git-Based Version Tracking**: Every project has automatic Git version control - industry standard, robust, and efficient
- **Tool Usage Transparency**: See exactly what the agent is doing
- **Background Maintenance**: Cloud AI keeps your workspace organized
- **Timeline View**: Track your session history and file changes
- **Semantic Search**: Find content by meaning, not just keywords

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Rust](https://rustup.rs/) (v1.70+)
- [Python](https://python.org/) (v3.10+)
- [Ollama](https://ollama.ai/) with Gemma model

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd AgentManager
   ```

2. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Build Rust Core**
   ```bash
   cd rust-core
   # For development (faster builds):
   cargo build
   # For production (optimized):
   cargo build --release
   ```

4. **Install Python Services**
   ```bash
   cd python-services
   uv venv .venv
   uv sync --group main-agent --group maintenance-agent --group embeddings
   ```

5. **Install Ollama and Gemma**
   ```bash
   # Install Ollama (see https://ollama.ai)
   ollama pull gemma:7b
   ```

### Running the Application

1. **Start Ollama**
   ```bash
   ollama serve
   ```

2. **Start Python Services**
   ```bash
   # In separate terminals:
   cd python-services/main_agent && python main.py
   cd python-services/maintenance_agent && python main.py
   cd python-services/embeddings && python main.py

   # PowerShell
   cd python-services/main_agent; python main.py
   cd python-services/maintenance_agent; python main.py
   cd python-services/embeddings; python main.py
   ```

3. **Start Rust Core**
   ```bash
   cd rust-core
   # Development mode (faster startup):
   cargo run
   # Production mode (optimized):
   cargo run --release
   ```

4. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

5. **Open** http://localhost:3000

## Project Structure

```
AgentManager/
├── frontend/                 # React/TypeScript UI
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/           # Custom hooks
│   │   └── styles/          # CSS/Tailwind
│   └── package.json
├── rust-core/               # Rust backend
│   ├── src/
│   │   ├── main.rs          # Entry point
│   │   ├── api.rs           # REST endpoints
│   │   ├── websocket.rs     # WebSocket handling
│   │   ├── workspace.rs     # Project management
│   │   └── ...
│   └── Cargo.toml
├── python-services/         # Python AI services
│   ├── main_agent/          # Chat agent (Ollama)
│   ├── maintenance_agent/   # Background maintenance
│   └── embeddings/          # Vector embeddings
└── files/                   # Design documents
```

## Configuration

### Environment Variables

```bash
# Ollama settings
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma:7b

# Cloud AI (optional, for maintenance agent)
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key

# Embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Development

### Frontend Development
```bash
cd frontend
npm run dev    # Development server
npm run build  # Production build
npm run lint   # Lint code
```

### Rust Development
```bash
cd rust-core
cargo run      # Development
cargo test     # Run tests
cargo clippy   # Lint code
```

### Python Development
```bash
cd python-services/main_agent
python main.py                    # Run service
python -m pytest                  # Run tests
```

## Git-Based Version Tracking

AgentManager uses **Git** for automatic version control. Each project gets its own Git repository that tracks all file changes made by the agent.

### How It Works

- **Auto-Commit**: Every file modification is automatically committed to Git
- **Project-Wide Tracking**: Git tracks the entire project, not just individual files
- **Standard Git Repository**: Each project has a `.git` directory with full version history
- **Industry Standard**: Leverages the battle-tested Git version control system

### Benefits

- ✅ **Robust**: Battle-tested Git handles all edge cases
- ✅ **Efficient**: Delta compression minimizes storage
- ✅ **Standard**: Use any Git tool to inspect history
- ✅ **Professional**: Same VCS used by millions of developers

### API Endpoints

The REST API provides access to Git history:

#### List All Versions of a File
```bash
GET /api/projects/:id/versions/:path
```

Returns version history from Git commits.

#### Get a Specific Version
```bash
GET /api/projects/:id/version/:version/:path
```

Retrieves content from a specific Git commit.

#### Restore a File to a Previous Version
```bash
POST /api/projects/:id/restore/:version/:path
```

Restores file content from a previous Git commit.

### Example Usage

```bash
# List versions of a file (via API)
curl http://localhost:8000/api/projects/PROJECT_ID/versions/myfile.txt

# Or use Git directly
cd ~/.agent-workspace/projects/PROJECT_ID
git log --oneline
git show {commit-hash}:myfile.txt
```

### Advanced: Direct Git Access

Since each project is a Git repository, you can use standard Git commands:

```bash
cd ~/.agent-workspace/projects/{PROJECT_ID}

# View commit history
git log --all --graph --oneline

# See what changed in a commit
git show {commit-hash}

# View file at specific commit
git show {commit-hash}:path/to/file.txt

# Create a branch for experiments
git checkout -b experiment
```

See `GIT_INTEGRATION.md` for complete documentation.

## License

MIT License - See LICENSE file for details.
