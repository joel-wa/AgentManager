```mermaid
flowchart TD
    A[Agent Response] --> B{Contains JSON?}
    
    B -->|Yes| C[Try Pattern 1:<br/>```json...```]
    B -->|No| M[Try Legacy Patterns]
    
    C --> D{Valid JSON?}
    D -->|Yes| E{Has tool_calls<br/>array?}
    D -->|No| F[Try Pattern 2:<br/>```...tool_calls...```]
    
    E -->|Yes| G{Each call has<br/>name + arguments?}
    E -->|No| F
    
    G -->|Yes| H[✅ Tool Calls<br/>Extracted!]
    G -->|No| F
    
    F --> I{Valid JSON?}
    I -->|Yes| J{Has tool_calls?}
    I -->|No| K[Try Pattern 3:<br/>Raw JSON]
    
    J -->|Yes| H
    J -->|No| K
    
    K --> L{Valid JSON?}
    L -->|Yes| N{Has tool_calls?}
    L -->|No| M
    
    N -->|Yes| H
    N -->|No| M
    
    M --> O[Check:<br/>[TOOL: name...]]
    M --> P[Check:<br/>&lt;tool&gt;name&lt;/tool&gt;]
    
    O --> Q{Found?}
    P --> Q
    
    Q -->|Yes| R[⚠️ Legacy Format<br/>Parsed]
    Q -->|No| S[❌ No Tool<br/>Calls Found]
    
    R --> T[Natural Language<br/>Response]
    H --> U[Execute Tools]
    S --> T
    
    U --> V[Return Results<br/>to Agent]
    V --> W[Agent Provides<br/>Final Answer]
    
    style H fill:#90EE90
    style R fill:#FFD700
    style S fill:#FFB6C6
    style U fill:#87CEEB
    style T fill:#DDA0DD
    
    classDef success fill:#90EE90,stroke:#2E8B57,stroke-width:2px
    classDef warning fill:#FFD700,stroke:#FF8C00,stroke-width:2px
    classDef error fill:#FFB6C6,stroke:#DC143C,stroke-width:2px
    
    class H success
    class R warning
    class S error
```

# Tool Call Parsing Flow

## 📊 How the System Detects Tool Calls

This diagram shows how the system parses agent responses to detect tool calls.

### 🎯 Parsing Priority Order

1. **Pattern 1 (Preferred):** ` ```json {...} ``` ` 
   - Standard markdown JSON code block
   - Most reliable and clear

2. **Pattern 2 (Fallback):** ` ```{..."tool_calls"...}``` `
   - Code block containing tool_calls (any language)
   - Less strict but still structured

3. **Pattern 3 (Fallback):** `{..."tool_calls"...}`
   - Raw JSON without code block markers
   - Risky but supported

4. **Legacy Patterns (Last Resort):**
   - `[TOOL: tool_name(...)]`
   - `<tool>tool_name(...)</tool>`
   - **Less reliable, avoid using**

### ✅ What Makes a Valid Tool Call

For JSON patterns (1-3), the system checks:

```
✓ Valid JSON syntax
  ↓
✓ Has "tool_calls" key
  ↓
✓ "tool_calls" is an array
  ↓
✓ Each item has "name" field
  ↓
✓ Each item has "arguments" field
  ↓
✓ Tool name exists in available tools
  ↓
✅ SUCCESS - Tool will be executed
```

### ❌ What Causes Parsing Failures

Common reasons tool calls are missed:

1. **Invalid JSON Syntax**
   ```json
   {
     name: "search",  // ❌ Missing quotes
     arguments: {query: test}  // ❌ Missing quotes
   }
   ```

2. **Missing Structure**
   ```json
   {
     "name": "search",  // ❌ No tool_calls wrapper
     "arguments": {"query": "test"}
   }
   ```

3. **Mixed Content**
   ```
   Let me search for that.  // ❌ Extra text
   ```json
   {"tool_calls": [...]}
   ```
   ```

4. **Missing Required Fields**
   ```json
   {
     "tool_calls": [
       {"name": "search"}  // ❌ No arguments field
     ]
   }
   ```

### 🔄 Complete Flow Example

**User:** "Read the README file"

**Agent Response (Correct):**
```json
{
  "tool_calls": [
    {
      "name": "read_file",
      "arguments": {"path": "README.md"}
    }
  ]
}
```

**System Processing:**
1. ✓ Finds JSON in markdown code block
2. ✓ Validates JSON syntax
3. ✓ Finds "tool_calls" array
4. ✓ Validates structure (name + arguments)
5. ✓ Checks tool name exists
6. ✅ **Executes read_file("README.md")**

**System Returns:**
```
[TOOL RESULTS]
read_file({"path":"README.md"}): File read successfully.
Content: # Agent Manager...

[END TOOL RESULTS]
```

**Agent Response (Natural Language):**
```
Based on the README, this is an Agent Manager system that helps
organize workspace files using AI...
```

### 💡 Pro Tips for Agents

1. **Always use Pattern 1** (JSON in markdown code block)
   - Most explicit and reliable
   - Easy for humans to read too

2. **No extra text** when calling tools
   - System expects ONLY JSON
   - Save your explanation for after results

3. **Validate before sending**
   - Check JSON syntax
   - Verify all required fields
   - Confirm tool names are correct

4. **Multiple tools at once**
   - More efficient than sequential calls
   - Add multiple objects to tool_calls array

5. **After tool results**
   - Switch to natural language
   - Explain what you found
   - Answer the user's question

### 🧪 Testing Your Understanding

**Question:** Which of these will work?

A)
```json
{
  "tool_calls": [
    {"name": "search", "arguments": {"query": "test"}}
  ]
}
```

B)
```
I'll search for that.
```json
{"tool_calls": [{"name": "search", "arguments": {"query": "test"}}]}
```
```

C)
```json
{"name": "search", "arguments": {"query": "test"}}
```

**Answer:** Only **A** will work correctly!
- **A** ✅ Perfect format
- **B** ❌ Has extra text before JSON
- **C** ❌ Missing tool_calls wrapper array

### 📚 Related Documentation

- Full guide: [TOOL_CALLING_GUIDE.md](./TOOL_CALLING_GUIDE.md)
- Quick reference: [TOOL_CALLING_QUICK_REF.md](./TOOL_CALLING_QUICK_REF.md)
- System fixes: [TOOL_SYSTEM_FIXES.md](./TOOL_SYSTEM_FIXES.md)
