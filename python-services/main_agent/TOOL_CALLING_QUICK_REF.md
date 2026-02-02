# Tool Calling Quick Reference Card

## ✅ CORRECT FORMAT

```json
{
  "tool_calls": [
    {
      "name": "tool_name",
      "arguments": {
        "arg1": "value1"
      }
    }
  ]
}
```

**Rules:**
1. Wrap in ` ```json ... ``` ` code block
2. Must have `tool_calls` array
3. Each call needs `name` AND `arguments`
4. No text before or after the JSON
5. Valid JSON syntax (double quotes, commas)

---

## ❌ COMMON MISTAKES

### Mistake 1: Extra Text
```
❌ Let me search for that.
```json
{"tool_calls": [...]}
```
```

### Mistake 2: Missing Wrapper
```json
❌ {
  "name": "search",
  "arguments": {"query": "test"}
}
```

### Mistake 3: Missing Arguments
```json
❌ {
  "tool_calls": [
    {"name": "read_file"}
  ]
}
```

### Mistake 4: Wrong Structure
```
❌ [TOOL: search("query")]
❌ <tool>search("query")</tool>
```

---

## 🔄 WORKFLOW

1. **Need info?** → Use tools (JSON only)
2. **Got results?** → Answer naturally
3. **Need more?** → Use tools again (JSON only)
4. **Done?** → Give final answer (natural language)

---

## 🎯 TOOL LIST

| Tool | Required Args |
|------|---------------|
| **search** | query |
| **read_file** | path |
| **write_file** | path, content |
| **list_directory** | path |
| **execute_command** | command |
| **find_recents** | - |
| **create_directory** | path |
| **delete_file** | path |

---

## 💡 QUICK EXAMPLES

### Single Tool
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

### Multiple Tools
```json
{
  "tool_calls": [
    {
      "name": "read_file",
      "arguments": {"path": "file1.md"}
    },
    {
      "name": "read_file",
      "arguments": {"path": "file2.md"}
    }
  ]
}
```

### Write File
```json
{
  "tool_calls": [
    {
      "name": "write_file",
      "arguments": {
        "path": "notes/new.md",
        "content": "# My Notes\n\nContent here"
      }
    }
  ]
}
```

---

## 🧪 CHECKLIST BEFORE RESPONDING

When calling tools, verify:

- [ ] Response is ONLY JSON (no extra text)
- [ ] Wrapped in ` ```json ... ``` `
- [ ] Has `tool_calls` array
- [ ] Each call has `name` and `arguments`
- [ ] All required args included
- [ ] Valid JSON (quotes, commas)
- [ ] Correct tool name (no typos)

**If all ✅ → Your tool call will work!**
