# Architecture of Fixes

## Fix 1: Custom Project Location Flow

### Before (Broken) ❌
```
User creates project with custom location
    ↓
create_project() uses custom path ✓
    ↓
Project files created at custom location ✓
    ↓
User tries to list files
    ↓
list_files() uses hardcoded path ❌
    ↓
ERROR: Files not found (looking in wrong location)
```

### After (Fixed) ✅
```
User creates project with custom location
    ↓
create_project() stores location in project.json ✓
    {
      "id": "abc123",
      "name": "My Project",
      "location": "/tmp/my-project"  ← Stored!
    }
    ↓
User tries to list files
    ↓
list_files() loads project from metadata ✓
    ↓
get_project_dir() checks project.location ✓
    ↓
Returns custom location if set, default otherwise ✓
    ↓
Files listed successfully from correct location ✓
```

### Code Path
```rust
// Step 1: Create project with location
let project = Project::new(name, description)
    .with_location(Some("/tmp/my-project"));

// Step 2: Save project (location stored in .meta/project.json)
workspace.create_project(&project)?;

// Step 3: Later - list files
let project = workspace.get_project(project_id)?;  // Load from metadata
let project_dir = workspace.get_project_dir(&project);  // Uses project.location

// Step 4: Read file
let file_path = project_dir.join("test.txt");
fs::read_to_string(file_path)?;
```

---

## Fix 2: Real-Time Streaming Flow

### Before (No Streaming) ❌
```
User sends message
    ↓
Frontend calls /api/chat (non-streaming)
    ↓
Backend processes entire request
    ↓
Agent runs all tool calls
    ↓
...wait...wait...wait...
    ↓
Complete response returned
    ↓
User finally sees result (could be minutes later)
```

### After (Streaming) ✅
```
User sends message
    ↓
Frontend calls /api/chat/stream (SSE)
    ↓
Backend streams events in real-time:
    ├─→ data: {"type":"status","message":"Processing..."}
    │   User sees: "Processing..." immediately
    │
    ├─→ data: {"type":"iteration","number":1}
    │   User sees: "[Iteration 1]"
    │
    ├─→ data: {"type":"tool_call","name":"list_directory"}
    │   User sees: "🔧 list_directory..."
    │
    ├─→ data: {"type":"tool_result","success":true}
    │   User sees: "✓ list_directory completed"
    │
    ├─→ data: {"type":"response","content":"Here are the files..."}
    │   User sees: Full response text
    │
    └─→ data: {"type":"done","message_id":"xyz"}
        User sees: Final message with complete data
```

### Event Flow
```typescript
// Frontend creates placeholder message immediately
const placeholder = {
  id: 'msg-123',
  content: '',  // Empty initially
  ...
}
setMessages([...messages, placeholder])

// Stream events update placeholder in real-time
api.sendMessageStream(request,
  // onEvent callback - called for each SSE event
  (event) => {
    if (event.type === 'tool_call') {
      content += `\n🔧 ${event.name}...`
      // Update placeholder message
      setMessages(prev => prev.map(m => 
        m.id === placeholder.id 
          ? { ...m, content }
          : m
      ))
    }
  },
  // onComplete - final response
  (response) => {
    // Replace placeholder with final message
    setMessages(prev => prev.map(m =>
      m.id === placeholder.id
        ? { ...m, content: response.response }
        : m
    ))
  }
)
```

---

## Network Protocol Comparison

### Non-Streaming (Before)
```http
POST /api/chat
Content-Type: application/json

{"message": "list files", "tools": ["list_directory"]}

→ Client waits... (15 seconds)

← HTTP 200 OK
  {"response": "Here are the files...", "message_id": "xyz"}
```

### Streaming (After)
```http
POST /api/chat/stream
Content-Type: application/json

{"message": "list files", "tools": ["list_directory"]}

← HTTP 200 OK
  Content-Type: text/event-stream

← data: {"type":"status","message":"Processing..."}     [0.1s]

← data: {"type":"tool_call","name":"list_directory"}    [0.2s]

← data: {"type":"tool_result","success":true}           [2.0s]

← data: {"type":"response","content":"Files..."}        [2.5s]

← data: {"type":"done","message_id":"xyz"}              [2.6s]
```

**Key Difference**: 
- Before: Wait 15s → See everything at once
- After: See updates every 0.1-2s → Real-time feedback

---

## User Experience Impact

### Scenario: Agent reading 5 files and analyzing them

**Before (No Streaming)**:
```
User: "Read all markdown files and summarize them"
[Sends message]
[Sees loading dots: ...]
[Waits 30 seconds]
[Finally sees complete response]

Timeline:
0s  ─────────────────────────────────── 30s
|                                         |
Send                                    Response
```

**After (With Streaming)**:
```
User: "Read all markdown files and summarize them"
[Sends message]
[Immediately sees: "Processing..."]
[0.5s] "🔧 list_directory..."
[1s] "✓ list_directory completed"
[1.5s] "🔧 read_file (file1.md)..."
[3s] "✓ read_file completed"
[3.5s] "🔧 read_file (file2.md)..."
[5s] "✓ read_file completed"
...
[28s] [Sees final summary appear]

Timeline:
0s ─ 1s ─ 3s ─ 5s ─ ... ─ 28s
|    |    |    |          |
Send │    │    │       Response
     Tool updates appear
```

**Result**: User knows what's happening, doesn't wonder if system is frozen.

---

## Implementation Details

### Custom Location: Key Files Changed

1. **`rust-core/src/models.rs`**
   ```rust
   pub struct Project {
       pub location: Option<String>,  // NEW
   }
   ```

2. **`rust-core/src/workspace.rs`**
   ```rust
   fn get_project_dir(&self, project: &Project) -> PathBuf {
       if let Some(location) = &project.location {
           PathBuf::from(location)  // Use custom
       } else {
           self.workspace_root.join("projects").join(&project.id)  // Use default
       }
   }
   ```

### Streaming: Key Files Changed

1. **`frontend/src/services/api.ts`**
   ```typescript
   async sendMessageStream(
     request: ChatRequest,
     onEvent: (event: StreamEvent) => void,  // Real-time callback
     onComplete: (response: ChatResponse) => void,
     onError: (error: Error) => void
   )
   ```

2. **`frontend/src/App.tsx`**
   ```typescript
   // Create placeholder that updates in real-time
   await api.sendMessageStream(request,
     (event) => updatePlaceholder(event),  // Called many times
     (final) => replacePlaceholder(final)   // Called once at end
   )
   ```

---

## Backward Compatibility

Both fixes maintain backward compatibility:

✅ **Custom Location**:
- Projects without `location` field → Use default path
- Old projects continue working
- No migration needed

✅ **Streaming**:
- Non-streaming endpoint (`/api/chat`) still exists
- Can fall back if streaming fails
- Progressive enhancement

