# Agent Manager - Production Deployment

## Quick Start

### Option 1: One-Click Launch (Recommended)

```powershell
.\build-app.ps1     # Build everything once
.\start-app.ps1     # Start the application
```

Then open: **http://localhost:5173**

### Option 2: Development Mode

```powershell
# Terminal 1 - Rust Core
cd rust-core
cargo run --release

# Terminal 2 - Main Agent
cd python-services/main_agent
python main.py

# Terminal 3 - Embeddings
cd python-services/embeddings
python main.py

# Terminal 4 - Frontend
cd frontend
npm run dev
```

---

## Production Build

### 1. Build the Application

```powershell
.\build-app.ps1
```

This will:
- Build the React frontend to static files (`frontend/dist`)
- Use existing Rust release binary (no rebuild needed)
- Install Python dependencies

### 2. Start All Services

```powershell
.\start-app.ps1
```

This launches:
- **Rust Core API** (port 8000) - Main backend coordinator
- **Main Agent Service** (port 8001) - AI agent with Ollama
- **Embeddings Service** (port 8002) - Vector embeddings
- **Frontend** (port 5173) - React web UI

Press `Ctrl+C` to stop all services.

---

## Architecture

```
┌─────────────────┐
│   Frontend      │  Port 5173 (Vite dev server)
│   (React)       │  or served from Rust in production
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Rust Core     │  Port 8000
│   (Coordinator) │  ← Main entry point
└────┬────────┬───┘
     │        │
     ↓        ↓
┌─────────┐  ┌──────────────┐
│ Main    │  │ Embeddings   │
│ Agent   │  │ Service      │
│ (AI)    │  │ (Vectors)    │
└─────────┘  └──────────────┘
Port 8001     Port 8002
```

---

## Deployment Options

### Option A: Standalone Web App (Current)

**Pros:**
- Simple to run
- No installation needed
- Uses existing browser

**Cons:**
- Requires terminal running
- Multiple processes

**How to distribute:**
1. Copy entire folder
2. User runs `build-app.ps1` then `start-app.ps1`

### Option B: Electron Desktop App

Convert to desktop app with:
```powershell
npm install -g electron-packager
# Add electron wrapper
electron-packager . AgentManager --platform=win32 --arch=x64
```

**Pros:**
- Single executable
- Native app experience
- No terminal needed

### Option C: Docker Compose

```yaml
version: '3'
services:
  rust-core:
    build: ./rust-core
    ports: ["8000:8000"]
  
  main-agent:
    build: ./python-services/main_agent
    ports: ["8001:8001"]
  
  embeddings:
    build: ./python-services/embeddings
    ports: ["8002:8002"]
```

**Pros:**
- Isolated environment
- Easy to deploy to cloud
- Consistent across machines

### Option D: Single Binary with Embedded Frontend

Modify Rust to serve static files:

```rust
// In rust-core/src/main.rs
use axum::Router;
use tower_http::services::ServeDir;

let app = Router::new()
    .nest_service("/", ServeDir::new("../frontend/dist"))
    .nest("/api", api_routes());
```

**Pros:**
- Single executable
- No separate frontend server
- Easiest distribution

---

## Current Status

✅ Frontend builds to static files  
✅ Rust binary exists (release mode)  
✅ Python services work independently  
✅ Launcher script coordinates all services  

**Ready for:**
- Local deployment (current setup)
- Server deployment (add systemd/Windows service)
- Docker containerization
- Electron wrapper

---

## Distribution Checklist

If you want to give this to someone else:

### Minimal Package (Current)
```
AgentManager/
├── start-app.ps1          # ← Double-click to run
├── build-app.ps1          # ← Run once first
├── rust-core/
│   └── target/release/
│       └── agent-workspace-core.exe
├── python-services/
│   ├── main_agent/
│   └── embeddings/
└── frontend/
    └── dist/              # ← Built static files
```

### Full Source Package
Everything in the repo

---

## Next Steps

### Make it More "App-Like"

1. **Add installer script:**
   - Check dependencies (Python, Node.js)
   - Auto-install Python packages
   - Create desktop shortcut

2. **Package as Electron:**
   - Bundle into single `.exe`
   - No terminal window
   - Auto-start services

3. **Add system tray icon:**
   - Start/stop services
   - Show status
   - Quick access

4. **Serve frontend from Rust:**
   - Single port (8000)
   - No separate Vite server
   - Simpler architecture

### Recommended: Serve Frontend from Rust

This is the cleanest for production. Let me know if you want this setup.
