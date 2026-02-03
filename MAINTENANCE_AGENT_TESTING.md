# Maintenance Agent Implementation Test Guide

## Testing Overview

This guide provides manual testing steps to verify the maintenance agent implementation.

## Prerequisites

1. All services must be running:
   - Rust Core (port 3000)
   - Main Agent (port 8001)
   - Embeddings (port 8003)
   - Maintenance Agent (port 8004)

## Test Cases

### Test 1: Health Check

```bash
# Test maintenance agent is running
curl http://localhost:8004/health
```

Expected: `{"status": "healthy", "cloud_available": true/false}`

### Test 2: Conversation Context Tracking

```bash
# Send a test message to track
curl -X POST http://localhost:8004/maintenance/context/message \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-project",
    "role": "user",
    "content": "I want to implement JWT authentication"
  }'
```

Expected: `{"status": "tracked"}`

### Test 3: File Change Notification

```bash
# Simulate a file change
curl -X POST http://localhost:8004/maintenance/file-change \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-project",
    "file_path": "auth/strategy.md",
    "change_type": "modified"
  }'
```

Expected: `{"status": "processing"}`

### Test 4: Get Suggestions

```bash
# Get pending suggestions for a project
curl http://localhost:8004/maintenance/suggestions/test-project
```

Expected: `{"suggestions": [...]}`

### Test 5: Workspace Analysis

```bash
# Analyze workspace
curl -X POST http://localhost:8004/maintenance/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-project",
    "files": [
      {"name": "notes.md", "extension": "md"},
      {"name": "notes_v2.md", "extension": "md"}
    ]
  }'
```

Expected: Analysis response with health_score and suggestions

### Test 6: .meta Folder Visibility

**Frontend Test**:
1. Open the UI
2. Navigate to a project
3. Look for `.meta` folder in the file browser
4. It should now be visible (previously hidden)

### Test 7: Integration Test - Full Flow

1. Create a project in the UI
2. Send a message: "Let's create a config file"
3. Create a file via the UI: `config.json`
4. Wait a few seconds
5. Check if `Recents.md` was created/updated in the project folder
6. Check for suggestions: `curl http://localhost:8004/maintenance/suggestions/<project-id>`

## Expected Behaviors

✅ **Context Tracking**: Messages sent to main agent are forwarded to maintenance agent
✅ **File Change Detection**: File writes trigger maintenance agent notifications
✅ **Recents.md Updates**: Significant changes automatically update Recents.md
✅ **.meta Visibility**: .meta folder is now visible in file browser
✅ **Suggestion Storage**: Suggestions are persisted in SQLite database
✅ **Non-blocking**: Maintenance operations don't block main agent

## Database Inspection

To inspect the suggestions database:

```bash
sqlite3 python-services/maintenance_agent/.meta/suggestions.db
.tables
SELECT * FROM suggestions;
```

## Troubleshooting

### Maintenance Agent Not Starting

- Check if port 8004 is available
- Verify Python dependencies are installed
- Check logs for errors

### No Suggestions Generated

- Verify conversation context is being tracked
- Check if file changes are being detected
- Ensure cloud client is configured

### .meta Folder Still Hidden

- Verify Rust core rebuild completed
- Clear browser cache
- Check workspace.rs changes were applied

## Success Criteria

All following should work:
- [x] Maintenance agent starts on port 8004
- [x] Health check returns success
- [x] Context tracking accepts messages
- [x] File change notifications are processed
- [x] Suggestions are stored in database
- [x] .meta folder visible in UI
- [x] Non-blocking operations (main agent not affected)
