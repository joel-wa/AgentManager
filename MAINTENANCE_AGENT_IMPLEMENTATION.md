# Maintenance Agent - Complete Implementation Plan

**Date**: February 3, 2026  
**Status**: Ready for Implementation  
**Target Port**: 8004

## Executive Summary

This document provides a complete implementation plan to transform the maintenance agent from a minimal placeholder into a fully-functional background service that:
- Monitors conversation context when files change
- Provides intelligent workspace analysis using embeddings
- Maintains the Recents.md timeline automatically
- Shows .meta folder in UI for agent access
- Generates actionable maintenance suggestions

---

## Current State Analysis

### What Exists
✅ Basic FastAPI service structure  
✅ Cloud AI client (Anthropic, OpenAI)  
✅ Ollama integration with separate model config  
✅ Simple file analysis endpoints  
✅ Port 8004 configured (avoiding conflicts)

### Critical Gaps
❌ No embeddings integration for semantic similarity  
❌ No conversation context tracking  
❌ No Recents.md auto-updates  
❌ .meta folder hidden from UI  
❌ No file change event handling  
❌ Analyzer too simplistic (string matching only)  
❌ No persistent suggestion state  
❌ No actual fix execution

---

## Architecture Changes

### 1. Event-Driven Context System

**Problem**: Maintenance agent needs conversation context when files change, but can't be called on every message.

**Solution**: Implement file change listener that captures conversation history at the moment of file modification.

```python
# New component: context_tracker.py

class ConversationContext:
    """Track conversation history relevant to file changes"""
    
    def __init__(self):
        self.conversations: Dict[str, List[Message]] = {}  # project_id -> messages
        self.file_change_contexts: Dict[str, ContextSnapshot] = {}  # file_path -> snapshot
    
    def add_message(self, project_id: str, message: Message):
        """Called by main agent after each message"""
        if project_id not in self.conversations:
            self.conversations[project_id] = []
        self.conversations[project_id].append(message)
        
        # Keep last 50 messages per project
        if len(self.conversations[project_id]) > 50:
            self.conversations[project_id] = self.conversations[project_id][-50:]
    
    def capture_context_for_file_change(
        self, 
        project_id: str, 
        file_path: str,
        change_type: str
    ) -> ContextSnapshot:
        """Capture conversation context at file change moment"""
        recent_messages = self.conversations.get(project_id, [])[-10:]  # Last 10
        
        snapshot = ContextSnapshot(
            project_id=project_id,
            file_path=file_path,
            change_type=change_type,
            timestamp=datetime.utcnow(),
            conversation_summary=self._summarize_messages(recent_messages),
            key_decisions=self._extract_decisions(recent_messages),
            mentioned_files=self._extract_file_mentions(recent_messages)
        )
        
        self.file_change_contexts[file_path] = snapshot
        return snapshot
    
    def _summarize_messages(self, messages: List[Message]) -> str:
        """Use LLM to summarize conversation leading to change"""
        # Implementation: Call Ollama with prompt
        pass
    
    def _extract_decisions(self, messages: List[Message]) -> List[str]:
        """Extract key decisions from messages"""
        # Look for patterns: "decided to", "will use", "choosing", etc.
        pass
    
    def _extract_file_mentions(self, messages: List[Message]) -> List[str]:
        """Extract mentioned file paths"""
        # Regex patterns for file paths
        pass
```

### 2. File Change Event Handler

**Integration Point**: Rust core already has file watcher (`file_ops.rs`)

**Python Side Implementation**:

```python
# New component: file_monitor.py

class FileChangeMonitor:
    """Listen for file changes and trigger maintenance actions"""
    
    def __init__(
        self, 
        context_tracker: ConversationContext,
        analyzer: WorkspaceAnalyzer,
        cloud_client: CloudClient
    ):
        self.context_tracker = context_tracker
        self.analyzer = analyzer
        self.cloud_client = cloud_client
        self.pending_updates: Dict[str, PendingUpdate] = {}
    
    async def handle_file_change(
        self,
        project_id: str,
        file_path: str,
        change_type: str  # created, modified, deleted
    ):
        """Main handler for file change events"""
        
        # 1. Capture conversation context
        context = self.context_tracker.capture_context_for_file_change(
            project_id, file_path, change_type
        )
        
        # 2. Analyze change impact
        impact = await self._analyze_change_impact(
            project_id, file_path, change_type, context
        )
        
        # 3. Update Recents.md if significant
        if impact.significance >= 0.7:
            await self._update_recents(project_id, file_path, context, impact)
        
        # 4. Check for maintenance opportunities
        suggestions = await self._generate_suggestions_from_change(
            project_id, file_path, context, impact
        )
        
        # 5. Queue suggestions for user
        for suggestion in suggestions:
            await self._queue_suggestion(project_id, suggestion)
    
    async def _analyze_change_impact(
        self, 
        project_id: str,
        file_path: str,
        change_type: str,
        context: ContextSnapshot
    ) -> ChangeImpact:
        """Determine significance of the change"""
        
        prompt = f"""Analyze this file change:

File: {file_path}
Change Type: {change_type}
Recent Conversation: {context.conversation_summary}
Key Decisions: {', '.join(context.key_decisions)}

Rate significance (0-1) and identify:
1. What changed conceptually
2. Impact on other files
3. Whether this is a decision point
4. Suggested Recents.md entry

Return JSON."""

        response = await self.cloud_client.generate(
            prompt, 
            system="You are analyzing workspace changes. Return valid JSON only."
        )
        
        # Parse and return ChangeImpact
        pass
    
    async def _update_recents(
        self,
        project_id: str,
        file_path: str,
        context: ContextSnapshot,
        impact: ChangeImpact
    ):
        """Auto-update Recents.md with new entry"""
        
        recents_path = f"projects/{project_id}/Recents.md"
        
        # Read existing
        existing_content = await self._read_file(recents_path)
        
        # Generate entry
        entry = f"""## {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} - {impact.title}
**Context**: {impact.description}
**Changes**: {file_path}
**Decision**: {impact.decision or 'N/A'}
**Status**: {impact.status}

"""
        
        # Insert at top (after # Recent Activity header)
        updated_content = self._insert_recent_entry(existing_content, entry)
        
        # Write back
        await self._write_file(recents_path, updated_content)
```

### 3. Enhanced Analyzer with Embeddings

**Problem**: Current analyzer only does naive string matching.

**Solution**: Integrate with embeddings service for semantic similarity.

```python
# Enhanced: analyzer.py

class WorkspaceAnalyzer:
    """Enhanced workspace analyzer with semantic understanding"""
    
    def __init__(self, embeddings_url: str = "http://localhost:8003"):
        self.embeddings_url = embeddings_url
        self.similarity_threshold = 0.75
    
    async def analyze(
        self, 
        project_id: str,
        files: List[Dict[str, Any]],
        context: Optional[ContextSnapshot] = None
    ) -> Dict[str, Any]:
        """Enhanced analysis with semantic understanding"""
        
        result = {
            "project_id": project_id,
            "health_score": 1.0,
            "duplicates": [],
            "semantic_clusters": [],
            "outdated": [],
            "improvements": [],
            "stats": self._gather_stats(files)
        }
        
        # 1. Find semantic duplicates (not just name matching)
        result["duplicates"] = await self._find_semantic_duplicates(
            project_id, files
        )
        
        # 2. Cluster related files
        result["semantic_clusters"] = await self._cluster_related_files(
            project_id, files
        )
        
        # 3. Find outdated content using LLM
        result["outdated"] = await self._find_outdated_content(
            project_id, files, context
        )
        
        # 4. Calculate health score
        result["health_score"] = self._calculate_health(result)
        
        # 5. Generate context-aware improvements
        result["improvements"] = await self._suggest_improvements(
            result, context
        )
        
        return result
    
    async def _find_semantic_duplicates(
        self,
        project_id: str,
        files: List[Dict[str, Any]]
    ) -> List[DuplicateGroup]:
        """Find semantically similar files using embeddings"""
        
        duplicates = []
        
        # Query embeddings service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.embeddings_url}/semantic/similar",
                json={
                    "project_id": project_id,
                    "threshold": self.similarity_threshold
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                similar_pairs = data.get("similar_pairs", [])
                
                # Group into clusters
                duplicates = self._cluster_similar_pairs(similar_pairs)
        
        return duplicates
    
    async def _cluster_related_files(
        self,
        project_id: str,
        files: List[Dict[str, Any]]
    ) -> List[FileCluster]:
        """Group files by semantic similarity"""
        
        # Query embeddings for clustering
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.embeddings_url}/semantic/cluster",
                json={
                    "project_id": project_id,
                    "num_clusters": "auto"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    FileCluster(
                        topic=cluster["topic"],
                        files=cluster["files"],
                        coherence=cluster["coherence"]
                    )
                    for cluster in data.get("clusters", [])
                ]
        
        return []
    
    async def _find_outdated_content(
        self,
        project_id: str,
        files: List[Dict[str, Any]],
        context: Optional[ContextSnapshot]
    ) -> List[OutdatedItem]:
        """Find outdated content using LLM analysis"""
        
        # Sample file contents for analysis
        file_samples = await self._sample_files(project_id, files, max_files=20)
        
        prompt = f"""Analyze these files for outdated content:

{self._format_file_samples(file_samples)}

Recent context: {context.conversation_summary if context else 'N/A'}

Identify files with:
1. Old API versions
2. Deprecated patterns
3. Stale date references
4. Contradictions with recent decisions

Return JSON array of {{file, reason, confidence}}"""

        response = await self.cloud_client.generate(prompt)
        
        # Parse and return
        pass
```

### 4. Persistent Suggestion State

**Problem**: No tracking of suggestions, acceptances, or dismissals.

**Solution**: SQLite database for suggestion state.

```python
# New component: suggestion_store.py

import sqlite3
import json
from datetime import datetime

class SuggestionStore:
    """Persistent storage for maintenance suggestions"""
    
    def __init__(self, db_path: str = ".meta/suggestions.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                affected_files TEXT,  -- JSON array
                priority TEXT NOT NULL,
                status TEXT NOT NULL,  -- pending, accepted, dismissed, applied
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT  -- JSON object
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_status 
            ON suggestions(project_id, status)
        """)
        conn.commit()
        conn.close()
    
    def save_suggestion(self, suggestion: Suggestion):
        """Save or update suggestion"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO suggestions 
            (id, project_id, type, title, description, affected_files, 
             priority, status, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            suggestion.id,
            suggestion.project_id,
            suggestion.type,
            suggestion.title,
            suggestion.description,
            json.dumps(suggestion.affected_files or []),
            suggestion.priority,
            suggestion.status,
            suggestion.created_at.isoformat(),
            datetime.utcnow().isoformat(),
            json.dumps(suggestion.metadata or {})
        ))
        conn.commit()
        conn.close()
    
    def get_pending_suggestions(self, project_id: str) -> List[Suggestion]:
        """Get all pending suggestions for project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT * FROM suggestions 
            WHERE project_id = ? AND status = 'pending'
            ORDER BY priority DESC, created_at DESC
        """, (project_id,))
        
        suggestions = [self._row_to_suggestion(row) for row in cursor.fetchall()]
        conn.close()
        return suggestions
    
    def update_status(self, suggestion_id: str, new_status: str):
        """Update suggestion status"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE suggestions 
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (new_status, datetime.utcnow().isoformat(), suggestion_id))
        conn.commit()
        conn.close()
```

### 5. Suggestion Execution Engine

**Problem**: No way to actually execute accepted suggestions.

**Solution**: Action executor that can perform common fixes.

```python
# New component: suggestion_executor.py

class SuggestionExecutor:
    """Execute accepted maintenance suggestions"""
    
    async def execute(
        self,
        suggestion: Suggestion,
        project_id: str
    ) -> ExecutionResult:
        """Execute a suggestion and return result"""
        
        if suggestion.type == "merge":
            return await self._execute_merge(suggestion, project_id)
        elif suggestion.type == "outdated":
            return await self._execute_update(suggestion, project_id)
        elif suggestion.type == "organize":
            return await self._execute_organization(suggestion, project_id)
        else:
            return ExecutionResult(
                success=False,
                error="Unknown suggestion type"
            )
    
    async def _execute_merge(
        self,
        suggestion: Suggestion,
        project_id: str
    ) -> ExecutionResult:
        """Merge duplicate files"""
        
        files_to_merge = suggestion.affected_files
        
        # 1. Read all file contents
        contents = await self._read_files(project_id, files_to_merge)
        
        # 2. Use LLM to intelligently merge
        merged_content = await self._intelligent_merge(contents)
        
        # 3. Write to first file
        primary_file = files_to_merge[0]
        await self._write_file(project_id, primary_file, merged_content)
        
        # 4. Archive other files
        for file_path in files_to_merge[1:]:
            await self._archive_file(project_id, file_path)
        
        return ExecutionResult(
            success=True,
            changes=[
                f"Merged {len(files_to_merge)} files into {primary_file}",
                f"Archived: {', '.join(files_to_merge[1:])}"
            ]
        )
    
    async def _intelligent_merge(self, contents: List[FileContent]) -> str:
        """Use LLM to merge file contents intelligently"""
        
        prompt = f"""Merge these {len(contents)} files intelligently:

{self._format_contents(contents)}

Rules:
1. Preserve all unique information
2. Eliminate redundancy
3. Maintain logical structure
4. Add comment marking merge

Return the merged content."""

        return await self.cloud_client.generate(prompt)
```

---

## UI Fix: Show .meta Folder

### Current Issue
`.meta` folder is hidden in UI but accessible to agents.

**Location**: `rust-core/src/workspace.rs:219`

```rust
// Skip hidden files and .meta directory
if name.starts_with('.') {
    continue;
}
```

### Solution Options

#### Option A: Always Show .meta (Recommended)
```rust
// workspace.rs line ~219
// Skip hidden files EXCEPT .meta directory
if name.starts_with('.') && name != ".meta" {
    continue;
}
```

#### Option B: Show All Hidden Files with Visual Indicator
```rust
// Remove the skip entirely, add metadata
if name.starts_with('.') {
    // Add 'hidden' flag to FileItem
    is_hidden = true;
}
```

Then in FileBrowser.tsx, render with different styling:
```tsx
<div className={`flex items-center gap-2 ${item.is_hidden ? 'opacity-50' : ''}`}>
  {item.is_hidden && <EyeOff className="w-3 h-3" />}
  {/* rest of rendering */}
</div>
```

**Recommendation**: Option A - specifically show .meta since it's part of the system design.

---

## API Integration Points

### New Endpoints Needed

```python
# main.py additions

@app.post("/maintenance/context/message")
async def track_message(request: MessageContext):
    """Called by main agent after each message"""
    context_tracker.add_message(
        request.project_id,
        Message(
            role=request.role,
            content=request.content,
            timestamp=datetime.utcnow()
        )
    )
    return {"status": "tracked"}

@app.post("/maintenance/file-change")
async def handle_file_change(request: FileChangeEvent):
    """Called when file changes detected"""
    await file_monitor.handle_file_change(
        request.project_id,
        request.file_path,
        request.change_type
    )
    return {"status": "processing"}

@app.get("/maintenance/suggestions/{project_id}")
async def get_suggestions(project_id: str):
    """Get pending suggestions"""
    suggestions = suggestion_store.get_pending_suggestions(project_id)
    return {"suggestions": [s.to_dict() for s in suggestions]}

@app.post("/maintenance/suggestions/{suggestion_id}/accept")
async def accept_suggestion(suggestion_id: str):
    """Accept and execute suggestion"""
    suggestion = suggestion_store.get_by_id(suggestion_id)
    
    # Execute
    result = await suggestion_executor.execute(
        suggestion,
        suggestion.project_id
    )
    
    # Update status
    if result.success:
        suggestion_store.update_status(suggestion_id, "applied")
    
    return result.to_dict()

@app.post("/maintenance/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(suggestion_id: str):
    """Dismiss suggestion"""
    suggestion_store.update_status(suggestion_id, "dismissed")
    return {"status": "dismissed"}
```

### Main Agent Integration

**Location**: `python-services/main_agent/main.py`

Add after message processing:

```python
# After line ~160 (in chat endpoint)
async def chat(request: ChatRequest):
    # ... existing code ...
    
    # Track message with maintenance agent
    if request.project_id:
        await track_with_maintenance_agent(
            request.project_id,
            "user",
            request.message
        )
    
    # ... rest of processing ...
    
    # Track response
    if request.project_id and response:
        await track_with_maintenance_agent(
            request.project_id,
            "assistant",
            response
        )

async def track_with_maintenance_agent(
    project_id: str,
    role: str,
    content: str
):
    """Send message to maintenance agent for context tracking"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8004/maintenance/context/message",
                json={
                    "project_id": project_id,
                    "role": role,
                    "content": content
                },
                timeout=2.0  # Don't wait long
            )
    except:
        pass  # Don't fail if maintenance agent down
```

### Rust Core Integration

**Location**: `rust-core/src/api.rs`

After write_file (line ~276):

```rust
// After writing file
match state.workspace.write_file(&id, &path, &body) {
    Ok(_) => {
        // Notify maintenance agent of file change
        let maintenance_url = "http://localhost:8004/maintenance/file-change";
        let _ = notify_file_change(maintenance_url, &id, &path, "modified").await;
        
        (StatusCode::OK, Json(json!({"success": true})))
    }
    Err(e) => // ... existing error handling
}

async fn notify_file_change(
    url: &str,
    project_id: &str,
    file_path: &str,
    change_type: &str
) -> Result<(), Box<dyn std::error::Error>> {
    let client = reqwest::Client::new();
    let _ = client
        .post(url)
        .json(&json!({
            "project_id": project_id,
            "file_path": file_path,
            "change_type": change_type
        }))
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await;
    Ok(())
}
```

---

## File Structure

```
python-services/maintenance_agent/
├── main.py                      # Main FastAPI app (enhanced)
├── cloud_client.py              # AI client (already has Ollama)
├── analyzer.py                  # Enhanced analyzer
├── summarizer.py                # Content summarizer (existing)
├── context_tracker.py           # NEW - Track conversation context
├── file_monitor.py              # NEW - Handle file change events
├── suggestion_store.py          # NEW - Persistent suggestion storage
├── suggestion_executor.py       # NEW - Execute suggestions
├── recents_updater.py           # NEW - Auto-update Recents.md
├── models.py                    # NEW - Data models
├── requirements.txt             # Updated dependencies
└── .meta/
    └── suggestions.db           # SQLite database
```

---

## Data Models

```python
# models.py

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Message(BaseModel):
    role: str  # user, assistant
    content: str
    timestamp: datetime

class ContextSnapshot(BaseModel):
    project_id: str
    file_path: str
    change_type: str  # created, modified, deleted
    timestamp: datetime
    conversation_summary: str
    key_decisions: List[str]
    mentioned_files: List[str]

class ChangeImpact(BaseModel):
    significance: float  # 0-1
    title: str
    description: str
    decision: Optional[str]
    status: str  # In Progress, Completed, etc.
    related_files: List[str]

class DuplicateGroup(BaseModel):
    files: List[str]
    similarity_score: float
    sample_content: str

class FileCluster(BaseModel):
    topic: str
    files: List[str]
    coherence: float  # 0-1

class OutdatedItem(BaseModel):
    file: str
    reason: str
    confidence: float
    suggested_fix: Optional[str]

class Suggestion(BaseModel):
    id: str
    project_id: str
    type: str  # merge, outdated, organize, update
    title: str
    description: str
    affected_files: Optional[List[str]]
    priority: str  # low, medium, high
    status: str  # pending, accepted, dismissed, applied
    created_at: datetime
    metadata: Optional[Dict[str, Any]]

class ExecutionResult(BaseModel):
    success: bool
    changes: Optional[List[str]]
    error: Optional[str]

class MessageContext(BaseModel):
    project_id: str
    role: str
    content: str

class FileChangeEvent(BaseModel):
    project_id: str
    file_path: str
    change_type: str  # created, modified, deleted
```

---

## Dependencies

Update `requirements.txt`:

```txt
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
httpx>=0.25.0
aiofiles>=23.2.1
python-multipart>=0.0.6
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure (Priority 1)
- [ ] Create `models.py` with all data models
- [ ] Create `suggestion_store.py` with SQLite persistence
- [ ] Create `context_tracker.py` for conversation tracking
- [ ] Create `file_monitor.py` for file change handling
- [ ] Update `main.py` with new endpoints

### Phase 2: Analyzer Enhancement (Priority 1)
- [ ] Enhance `analyzer.py` with embeddings integration
- [ ] Add semantic duplicate detection
- [ ] Add semantic clustering
- [ ] Add LLM-based outdated content detection
- [ ] Improve health score calculation

### Phase 3: Automation (Priority 2)
- [ ] Create `suggestion_executor.py` for fix execution
- [ ] Implement merge execution
- [ ] Implement update execution
- [ ] Implement organization execution
- [ ] Create `recents_updater.py` for timeline maintenance

### Phase 4: Integration (Priority 1)
- [ ] Add message tracking to main agent
- [ ] Add file change notification to Rust core
- [ ] Update `.meta` folder visibility in workspace.rs
- [ ] Test end-to-end flow

### Phase 5: UI Integration (Priority 2)
- [ ] Verify .meta folder shows in FileBrowser
- [ ] Add suggestion notification system
- [ ] Add suggestion accept/dismiss UI
- [ ] Add Recents.md viewer

### Phase 6: Testing (Priority 1)
- [ ] Test conversation context capture
- [ ] Test file change detection
- [ ] Test Recents.md auto-updates
- [ ] Test semantic duplicate detection
- [ ] Test suggestion execution
- [ ] Test with multiple simultaneous file changes

---

## Configuration

Add to project's `.meta/maintenance.json`:

```json
{
  "enabled": true,
  "context_tracking": {
    "enabled": true,
    "max_messages_per_project": 50,
    "context_window_on_change": 10
  },
  "analysis": {
    "similarity_threshold": 0.75,
    "min_significance_for_recents": 0.7
  },
  "recents": {
    "auto_update": true,
    "max_entries": 50
  },
  "suggestions": {
    "max_per_project": 10,
    "auto_archive_after_days": 30
  },
  "ai": {
    "provider": "ollama",
    "model": "kimi-k2.5:cloud",
    "fallback_to_cloud": true
  }
}
```

---

## Testing Scenarios

### Scenario 1: File Change with Context
1. User chats with main agent about authentication
2. User decides to use JWT tokens
3. Main agent writes to `auth/strategy.md`
4. **Expected**: Maintenance agent:
   - Captures last 10 messages about auth decision
   - Analyzes significance (high)
   - Updates Recents.md with entry:
     ```
     ## 2026-02-03 14:30 - JWT Authentication Decision
     **Context**: Discussing authentication approaches
     **Decision**: Implementing JWT tokens with RS256
     **Changes**: auth/strategy.md
     **Status**: In Progress
     ```

### Scenario 2: Duplicate Detection
1. User has files: `notes.md`, `notes-v2.md`, `notes_backup.md`
2. All have 80% similar content
3. **Expected**: Maintenance agent:
   - Detects semantic similarity via embeddings
   - Creates suggestion: "Merge 3 similar note files"
   - User accepts
   - Agent merges intelligently, archives old versions

### Scenario 3: Outdated Content
1. User has `api/v1-guide.md` mentioning old endpoints
2. Recent conversation shows switch to v2 API
3. **Expected**: Maintenance agent:
   - Detects contradiction between file and recent decisions
   - Suggests: "Update v1-guide.md to reflect v2 API changes"
   - Provides preview of suggested changes

---

## Performance Considerations

1. **Conversation Context**: Keep only last 50 messages per project in memory
2. **File Change Debouncing**: Wait 2 seconds after change before processing
3. **Embeddings Cache**: Cache embeddings, only regenerate on content change
4. **Async Processing**: All maintenance operations run async, don't block main agent
5. **Database**: SQLite with proper indexes for fast queries

---

## Future Enhancements (Post-MVP)

1. **Learning System**: Track suggestion acceptance rate, adapt recommendations
2. **Scheduled Analysis**: Periodic full-workspace health checks
3. **Smart Refactoring**: Suggest code refactorings based on patterns
4. **Multi-Agent Collaboration**: Coordinate with main agent on complex tasks
5. **Workspace Templates**: Learn from successful project structures
6. **Auto-Documentation**: Generate and update docs automatically

---

## Environment Variables

```bash
# Maintenance Agent Configuration
MAINTENANCE_OLLAMA_URL=http://127.0.0.1:11434
MAINTENANCE_OLLAMA_MODEL=kimi-k2.5:cloud

# Cloud AI (fallback)
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...

# Service URLs
EMBEDDINGS_SERVICE_URL=http://localhost:8003
MAIN_AGENT_URL=http://localhost:8001
RUST_CORE_URL=http://localhost:3000

# Features
MAINTENANCE_AUTO_RECENTS=true
MAINTENANCE_AUTO_SUGGESTIONS=true
```

---

## Success Metrics

After implementation, verify:

1. ✅ Conversation context captured on file changes
2. ✅ Recents.md auto-updates with significant changes
3. ✅ Semantic duplicate detection works (>75% similarity)
4. ✅ .meta folder visible in UI
5. ✅ Suggestions can be accepted/dismissed
6. ✅ Accepted suggestions execute correctly
7. ✅ No performance impact on main agent
8. ✅ Works with Ollama (no cloud API required)

---

## Notes for Implementation Agent

- **Start with Phase 1**: Get infrastructure working first
- **Test incrementally**: Each component should work standalone
- **Use existing patterns**: Follow structure from main_agent/
- **Error handling**: Maintenance agent failures should never break main agent
- **Logging**: Add comprehensive logging for debugging
- **Database migrations**: Create migration system for future schema changes

---

**Ready for Implementation** ✨

This document provides complete specifications for enhancing the maintenance agent. The implementation should be done in phases, with Phase 1 (infrastructure) and Phase 4 (integration) being highest priority.
