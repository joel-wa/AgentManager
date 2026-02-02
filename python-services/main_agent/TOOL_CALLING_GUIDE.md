# Tool Calling Guide for AI Agents

This guide shows the **correct** and **incorrect** ways for an AI agent to call tools in this system.

---

## ✅ CORRECT WAY: JSON Format with Code Blocks

When you need to use tools, respond **ONLY** with a JSON object in a markdown code block:

### Example 1: Single Tool Call

```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {
        "query": "project setup instructions",
        "max_results": 5
      }
    }
  ]
}
```

### Example 2: Multiple Tool Calls

```json
{
  "tool_calls": [
    {
      "name": "read_file",
      "arguments": {
        "path": "README.md"
      }
    },
    {
      "name": "read_file",
      "arguments": {
        "path": "package.json"
      }
    },
    {
      "name": "list_directory",
      "arguments": {
        "path": "src"
      }
    }
  ]
}
```

### Example 3: Writing a File

```json
{
  "tool_calls": [
    {
      "name": "write_file",
      "arguments": {
        "path": "notes/meeting-2025-02-02.md",
        "content": "# Meeting Notes\n\n- Discussed project timeline\n- Reviewed requirements\n- Next steps assigned"
      }
    }
  ]
}
```

---

## ❌ WRONG WAYS (Will Be Missed or Fail)

### ❌ Wrong 1: Mixing Text with JSON

**DON'T DO THIS:**
```
I'll search for that information now.

```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {"query": "setup"}
    }
  ]
}
```

After searching, I'll provide you with the results.
```

**WHY IT'S WRONG:** The system expects ONLY JSON when calling tools. Any extra text confuses the parser.

**CORRECT VERSION:** Just the JSON, nothing else:
```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {"query": "setup"}
    }
  ]
}
```

---

### ❌ Wrong 2: Missing Required Fields

**DON'T DO THIS:**
```json
{
  "tool_calls": [
    {
      "name": "read_file"
    }
  ]
}
```

**WHY IT'S WRONG:** Missing the `arguments` field. Every tool call MUST have both `name` and `arguments`, even if arguments is empty.

**CORRECT VERSION:**
```json
{
  "tool_calls": [
    {
      "name": "read_file",
      "arguments": {
        "path": "README.md"
      }
    }
  ]
}
```

---

### ❌ Wrong 3: Using Legacy Text Patterns

**DON'T DO THIS:**
```
[TOOL: search("project setup")]
```

or

```
<tool>search("project setup")</tool>
```

**WHY IT'S WRONG:** These legacy patterns are only supported for backward compatibility and are less reliable. The parser prefers JSON format.

**CORRECT VERSION:**
```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {
        "query": "project setup"
      }
    }
  ]
}
```

---

### ❌ Wrong 4: Malformed JSON

**DON'T DO THIS:**
```json
{
  "tool_calls": [
    {
      name: "search",  // Missing quotes around key
      arguments: {query: "test"}  // Missing quotes around keys/values
    }
  ]
}
```

**WHY IT'S WRONG:** Invalid JSON syntax. Keys and string values MUST be in double quotes.

**CORRECT VERSION:**
```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {
        "query": "test"
      }
    }
  ]
}
```

---

### ❌ Wrong 5: Wrong Structure

**DON'T DO THIS:**
```json
{
  "name": "search",
  "arguments": {"query": "test"}
}
```

**WHY IT'S WRONG:** Missing the `tool_calls` array wrapper. The system expects an object with a `tool_calls` array.

**CORRECT VERSION:**
```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {
        "query": "test"
      }
    }
  ]
}
```

---

### ❌ Wrong 6: Using Code Block Without Language Specifier

**DON'T DO THIS:**
````
```
{
  "tool_calls": [{"name": "search", "arguments": {"query": "test"}}]
}
```
````

**WHY IT'S WRONG:** While this might work, it's less clear. Always use ```json for consistency.

**CORRECT VERSION:**
````
```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {
        "query": "test"
      }
    }
  ]
}
```
````

---

### ❌ Wrong 7: Responding in Natural Language When Tools Are Needed

**DON'T DO THIS:**
```
To find that information, I need to search the workspace. Let me do that for you.
```

**WHY IT'S WRONG:** If you need to use a tool, don't just talk about it - USE IT!

**CORRECT VERSION:**
```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {
        "query": "the information I need"
      }
    }
  ]
}
```

---

## 📝 Complete Workflow Example

### User Request:
"Read the README.md file and tell me what this project does"

### ✅ CORRECT Agent Response (Step 1 - Tool Call):
```json
{
  "tool_calls": [
    {
      "name": "read_file",
      "arguments": {
        "path": "README.md"
      }
    }
  ]
}
```

### System Response (Tool Result):
```
[TOOL RESULTS]

read_file({"path":"README.md"}): File read successfully.
Content: # Agent Manager

This project is an AI-powered workspace management system...

[END TOOL RESULTS]
Now provide your answer based on these results.
```

### ✅ CORRECT Agent Response (Step 2 - Natural Language):
```
Based on the README.md file, this project is an **Agent Manager** - an AI-powered workspace management system. It helps users organize notes, research, and code files through an intelligent agent interface.

The system includes:
- A Rust core for high-performance file operations
- Python services for AI agent logic and embeddings
- A React frontend for user interaction

It's designed to provide an AI assistant that can search, read, write, and organize files in a workspace environment.
```

---

## 🎯 Key Rules Summary

1. **Use JSON format** - Always wrap tool calls in proper JSON structure
2. **Use markdown code blocks** - Wrap JSON in ` ```json ... ``` `
3. **Include tool_calls array** - Even for single tool calls
4. **Provide all required arguments** - Check the tool's parameter schema
5. **Valid JSON syntax** - Use double quotes, proper commas
6. **ONLY JSON when calling tools** - No extra text before or after
7. **Natural language AFTER results** - Respond normally once you have the information

---

## 🔍 Available Tools Reference

### 1. search
Search the workspace for content
```json
{
  "name": "search",
  "arguments": {
    "query": "string (required)",
    "max_results": 10  // optional, default: 10
  }
}
```

### 2. read_file
Read contents of a file
```json
{
  "name": "read_file",
  "arguments": {
    "path": "string (required)"
  }
}
```

### 3. write_file
Create or update a file
```json
{
  "name": "write_file",
  "arguments": {
    "path": "string (required)",
    "content": "string (required)"
  }
}
```

### 4. list_directory
List contents of a directory
```json
{
  "name": "list_directory",
  "arguments": {
    "path": "string (required)"
  }
}
```

### 5. execute_command
Execute a shell command
```json
{
  "name": "execute_command",
  "arguments": {
    "command": "string (required)",
    "cwd": "string (optional)"
  }
}
```

### 6. find_recents
Find recently modified files
```json
{
  "name": "find_recents",
  "arguments": {
    "days": 7,  // optional, default: 7
    "limit": 10  // optional, default: 10
  }
}
```

### 7. create_directory
Create a new directory
```json
{
  "name": "create_directory",
  "arguments": {
    "path": "string (required)"
  }
}
```

### 8. delete_file
Delete a file
```json
{
  "name": "delete_file",
  "arguments": {
    "path": "string (required)"
  }
}
```

---

## 🧪 Testing Your Tool Calls

Use this checklist before responding:

- [ ] Is my response ONLY JSON (no extra text)?
- [ ] Is it wrapped in ` ```json ... ``` `?
- [ ] Does it have a `tool_calls` array?
- [ ] Does each call have `name` AND `arguments`?
- [ ] Are all required arguments included?
- [ ] Is the JSON valid (quotes, commas, brackets)?
- [ ] Am I using the correct tool name?

If all checks pass, your tool call will work! ✅

---

## 💡 Pro Tips

### Multiple Related Tool Calls
When you need to read multiple files, call them all at once:

```json
{
  "tool_calls": [
    {
      "name": "read_file",
      "arguments": {"path": "src/main.ts"}
    },
    {
      "name": "read_file",
      "arguments": {"path": "src/utils.ts"}
    },
    {
      "name": "read_file",
      "arguments": {"path": "package.json"}
    }
  ]
}
```

### Relative vs Absolute Paths
Both work, but relative paths are cleaner:

```json
// ✅ Recommended - Relative path
{"path": "notes/meeting.md"}

// ✅ Also works - Absolute path
{"path": "/full/path/to/project/notes/meeting.md"}
```

### File Path Conventions
- Use forward slashes: `src/components/App.tsx`
- Don't include leading slash for relative paths: `notes/file.md` not `/notes/file.md`
- Use actual paths, not descriptions: `README.md` not `the readme file`

---

## 🚨 Common Parsing Errors

### Error: "Tool call not detected"
**Cause:** Extra text mixed with JSON or malformed JSON
**Fix:** Respond with ONLY the JSON code block

### Error: "Missing required argument: path"
**Cause:** Forgot to include required arguments
**Fix:** Check tool schema and include all required arguments

### Error: "Invalid JSON"
**Cause:** Syntax errors in JSON (missing quotes, commas, etc.)
**Fix:** Validate JSON structure - use a JSON validator if unsure

### Error: "Unknown tool: searh"
**Cause:** Typo in tool name
**Fix:** Double-check tool name spelling against available tools list

---

## 📚 Real-World Examples

### Example: User asks "What files are in the src directory?"

**❌ WRONG:**
```
Let me check the src directory for you.

I'll use the list_directory tool to see what's there.
```

**✅ CORRECT:**
```json
{
  "tool_calls": [
    {
      "name": "list_directory",
      "arguments": {
        "path": "src"
      }
    }
  ]
}
```

Then after seeing results:
```
The src directory contains the following files:
- main.ts
- App.tsx
- utils.ts
- components/ (directory)
- styles/ (directory)
```

---

### Example: User asks "Create a todo list file"

**❌ WRONG:**
```
I'll create a todo list file for you with some sample content.
```

**✅ CORRECT:**
```json
{
  "tool_calls": [
    {
      "name": "write_file",
      "arguments": {
        "path": "todo.md",
        "content": "# Todo List\n\n## Today\n- [ ] Review project requirements\n- [ ] Update documentation\n\n## This Week\n- [ ] Implement new features\n- [ ] Write tests"
      }
    }
  ]
}
```

Then after success:
```
I've created a todo.md file with a basic structure including sections for today and this week. You can edit it to add your specific tasks.
```

---

## 🎓 Remember

**When using tools:** Respond with **ONLY JSON** in proper format

**After tool results:** Respond with **natural language** like a helpful assistant

This separation is key to reliable tool calling!
