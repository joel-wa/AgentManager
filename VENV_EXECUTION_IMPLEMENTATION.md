# Temporary Venv Execution System

## Overview

The agent can now execute Python and pip commands in **project-specific temporary virtual environments**. This ensures package installations and Python executions are isolated per chat session/project.

## How It Works

### 1. **VenvManager Class**
- Manages virtual environments for each project
- Venvs are stored in: `~/.agent-workspace/venvs/{project_id}`
- Auto-creates venvs on first use
- Provides paths to Python and pip executables within each venv

### 2. **Enhanced ExecuteCommandTool**
- Automatically detects `python` and `pip` commands
- Transforms them to use the project's venv executables
- Creates venv on-demand if it doesn't exist
- Works on both Windows and Unix systems

### 3. **Integration**
- ToolExecutor passes `project_id` to all tools
- ExecuteCommandTool receives project_id and creates/uses appropriate venv
- Transparent to the agent - just uses standard commands

## Command Examples

The agent can now execute these commands, and they'll automatically use the project's venv:

```bash
# Python commands - uses project venv
python --version
python script.py
python -c "import requests; print(requests.__version__)"

# Pip commands - installs to project venv
pip install requests
pip install markdown2 pdfkit
pip install weasyprint markdown2
pip install reportlab markdown2
pip list
pip show requests

# Regular commands - not affected
dir
ls
git status
pandoc "file.md" -o "file.pdf"
```

## Command Transformation

When the agent calls `execute_command`:

### Before (without venv):
```json
{
  "command": "pip install requests"
}
```

### After (with venv):
```json
{
  "command": "\"C:\\Users\\RanVic\\.agent-workspace\\venvs\\project-123\\Scripts\\pip.exe\" install requests"  
}
```

The transformation is automatic and transparent!

## Architecture

```
User Message
    ↓
Main Agent (/agent/chat)
    ↓
ToolExecutor (with project_id)
    ↓
ToolRegistry (registers ExecuteCommandTool with project_id)
    ↓
ExecuteCommandTool
    ↓
VenvManager.ensure_venv()  ← Creates venv if needed
    ↓
Transform command  ← Replaces python/pip with venv paths
    ↓
Execute PowerShell/Bash
    ↓
Return Result
```

## File Changes

### Modified Files:
1. **tool_logic.py**
   - Added `VenvManager` class (handles venv lifecycle)
   - Enhanced `ExecuteCommandTool` with venv support
   - Updated `ToolRegistry` to pass `project_id`
   - Updated `ToolExecutor` to pass `project_id` to registry

### New Files:
1. **test_venv_execution.py** - Test script demonstrating the functionality

## Key Features

### ✅ Automatic Venv Creation
- First `python` or `pip` command triggers venv creation
- Takes ~5-10 seconds on first use
- Subsequent commands are instant

### ✅ Isolated Environments
- Each project gets its own venv
- Package installations don't affect system Python
- No conflicts between projects

### ✅ Windows & Unix Compatible
- Windows: Uses `Scripts\python.exe` and `Scripts\pip.exe`
- Unix: Uses `bin/python` and `bin/pip`

### ✅ Transparent to Agent
- Agent uses normal commands: `pip install package`
- No special syntax or activation required
- Works with existing agent prompts

### ✅ Persistent Per Chat
- Venv persists for the life of the project
- Packages remain installed across multiple messages
- Can be manually cleaned up if needed

## Usage Example

### Agent Workflow:
1. User: "Install weasyprint and convert this markdown to PDF"
2. Agent calls: `execute_command` with `pip install weasyprint`
3. System:
   - Checks if venv exists for project_id
   - Creates venv if needed (first time only)
   - Transforms command to use venv pip
   - Executes: `"~/.agent-workspace/venvs/abc123/Scripts/pip.exe" install weasyprint`
4. Agent calls: `execute_command` with `python convert.py`
5. System:
   - Transforms to use venv python
   - Executes: `"~/.agent-workspace/venvs/abc123/Scripts/python.exe" convert.py`
6. Python runs with weasyprint available!

## Venv Lifecycle

### Creation:
```python
venv_manager = VenvManager()
success, message = await venv_manager.create_venv("project-123")
```

### Check Existence:
```python
exists = venv_manager.venv_exists("project-123")
```

### Get Executables:
```python
python_exe = venv_manager.get_python_executable("project-123")
pip_exe = venv_manager.get_pip_executable("project-123")
```

### Cleanup (manual):
```python
success, message = venv_manager.delete_venv("project-123")
```

## Testing

Run the test script:
```bash
cd python-services/main_agent
python test_venv_execution.py
```

This will:
1. Create a test venv
2. Execute python/pip commands
3. Verify package installation
4. Show venv location for manual inspection

## Edge Cases Handled

### ✅ First-time venv creation timeout
- 60 second timeout for venv creation
- Clear error message if creation fails

### ✅ Command transformation
- Only transforms commands starting with `python ` or `pip `
- Case-insensitive detection
- Preserves rest of command exactly

### ✅ Non-Python commands
- Regular commands (git, dir, ls, etc.) passed through unchanged
- No performance impact for non-Python commands

### ✅ Working directory
- Commands execute in project directory
- Venv is separate from working directory
- Paths resolved correctly

## Benefits

1. **Isolation**: No conflicts between projects
2. **Cleanliness**: System Python remains untouched
3. **Reproducibility**: Each project has consistent environment
4. **Safety**: Failed installs don't break system
5. **Simplicity**: Agent doesn't need special configuration

## Future Enhancements

Possible additions:
- Venv cleanup on project deletion
- requirements.txt auto-generation
- Venv caching/sharing for common package sets
- Progress feedback during venv creation
- Environment variable support
- Conda environment support

## Configuration

### Default Venv Location:
```
~/.agent-workspace/venvs/
```

### Change Venv Location:
```python
venv_manager = VenvManager(venv_base_dir="/custom/path/venvs")
```

### Adjust Timeouts:
```python
execute_tool = ExecuteCommandTool(
    working_directory="/path",
    project_id="abc",
    timeout=120  # 2 minutes
)
```

## Troubleshooting

### Venv creation fails:
- Check Python installation: `python -m venv --help`
- Ensure disk space available
- Check permissions on ~/.agent-workspace/

### Commands not using venv:
- Verify project_id is being passed to ToolExecutor
- Check venv exists: Look in ~/.agent-workspace/venvs/
- Look for transformation logs in console output

### Package not found after install:
- Verify install succeeded (check stdout/stderr)
- Check venv python: `{venv}/Scripts/python.exe -m pip list`
- Ensure same project_id for install and run commands

## Summary

The implementation provides **transparent, automatic, per-project Python virtual environments** for the agent system. The agent can now safely install and use Python packages without worrying about:
- System pollution
- Dependency conflicts
- Manual activation
- Cross-project interference

Commands like `pip install weasyprint` just work, and the packages are available for subsequent Python commands in the same project!
