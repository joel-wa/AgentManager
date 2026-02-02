# Testing Guide for Fixed Issues

## Issue 1: Custom Project Location

### Manual Test Steps

1. **Start all services**:
   ```bash
   # Terminal 1: Start Rust core
   cd rust-core && cargo run
   
   # Terminal 2: Start Python agent
   cd python-services/main_agent && python main.py
   
   # Terminal 3: Start Frontend
   cd frontend && npm run dev
   ```

2. **Test Custom Location**:
   - Open http://localhost:3000
   - Click "New Project" (+) button
   - Enter project name: "Test Custom Location"
   - Check "Custom Location" checkbox
   - Enter a path like `/tmp/test-project` (or `C:\Temp\test-project` on Windows)
   - Click "Create Project"
   - Verify project is created at the specified location (check filesystem)
   - Create a file in the project (e.g., "test.txt")
   - Verify file appears in file browser
   - Edit and save the file
   - Verify file is saved at custom location (check filesystem)

3. **Expected Results**:
   - Project created at custom location with proper structure:
     ```
     /tmp/test-project/
       .meta/
         project.json (contains location field)
       files/
       notes/
       README.md
       soul.md
       Recents.md
     ```
   - All file operations work correctly
   - Files are read from and written to custom location

## Issue 2: Real-Time Streaming

### Manual Test Steps

1. **With services running** (see above)

2. **Test Streaming**:
   - Open http://localhost:3000
   - Select or create a project
   - Send a message that requires tool usage, e.g.:
     - "List all files in this project"
     - "Read the README file and tell me what it says"
     - "Create a new file called test.md with some content"
   
3. **Observe Streaming Behavior**:
   - As soon as you send message, you should see placeholder message appear
   - Watch for real-time updates:
     - Status messages (e.g., "Processing...")
     - Iteration indicators (e.g., "[Iteration 1]")
     - Tool call indicators (e.g., "🔧 list_directory...")
     - Tool completion indicators (e.g., "✓ list_directory completed")
   - Final response appears smoothly
   - No waiting for complete response before seeing anything

4. **Expected Results**:
   - User sees progress as agent works
   - Tool calls appear in real-time
   - No more "loading dots" waiting for everything
   - Smooth, responsive user experience

## Automated Test (Optional)

You can verify the streaming endpoint works:

```bash
# Test streaming endpoint directly
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "list files",
    "tools": ["list_directory"],
    "project_id": "test-project-id"
  }'
```

Expected output:
```
data: {"type":"status","message":"Processing your request..."}
data: {"type":"iteration","number":1}
data: {"type":"tool_call","name":"list_directory","arguments":{...}}
data: {"type":"tool_result","name":"list_directory","success":true,...}
data: {"type":"response","content":"Here are the files..."}
data: {"type":"done","message_id":"..."}
```

## Success Criteria

✅ Custom location projects can be created, read from, and written to
✅ File operations respect custom project locations
✅ Chat responses stream in real-time
✅ Tool calls and results appear as they happen
✅ No waiting for complete response before seeing updates
