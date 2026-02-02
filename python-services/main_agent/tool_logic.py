"""
Tool Logic
Extensible tool system for the agent with built-in and custom tools
"""

from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import subprocess
import os
import sys
import time


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


@dataclass
class ToolDefinition:
    """Definition of a tool with metadata"""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str = "general"
    requires_confirmation: bool = False
    

class BaseTool(ABC):
    """Base class for all tools - extend this to create new tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for parameters"""
        pass
    
    @property
    def category(self) -> str:
        """Tool category for organization"""
        return "general"
    
    @property
    def requires_confirmation(self) -> bool:
        """Whether tool requires user confirmation"""
        return False
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given arguments"""
        pass
    
    def to_definition(self) -> ToolDefinition:
        """Convert to tool definition"""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            category=self.category,
            requires_confirmation=self.requires_confirmation
        )


class SearchTool(BaseTool):
    """Search workspace for content"""
    
    @property
    def name(self) -> str:
        return "search"
    
    @property
    def description(self) -> str:
        return "Search the workspace for relevant content matching a query"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    
    @property
    def category(self) -> str:
        return "file_operations"
    
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        query = args.get("query", "")
        max_results = args.get("max_results", 10)
        # Delegated to Rust core via vector DB
        return ToolResult(
            success=True,
            result={
                "query": query,
                "max_results": max_results,
                "matches": [],
                "status": "delegated_to_core"
            }
        )


class ReadFileTool(BaseTool):
    """Read file contents"""
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read the contents of a file at the specified path"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file relative to workspace root"
                }
            },
            "required": ["path"]
        }
    
    @property
    def category(self) -> str:
        return "file_operations"
    
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        path = args.get("path", "")
        if not path:
            return ToolResult(
                success=False,
                result=None,
                error="No path provided"
            )
        
        try:
            # Read file asynchronously
            import aiofiles
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            return ToolResult(
                success=True,
                result={
                    "path": path,
                    "content": content,
                    "size_bytes": len(content.encode('utf-8'))
                }
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                result=None,
                error=f"File not found: {path}"
            )
        except PermissionError:
            return ToolResult(
                success=False,
                result=None,
                error=f"Permission denied: {path}"
            )
        except Exception as e:
            # Fallback to sync read if aiofiles not available
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return ToolResult(
                    success=True,
                    result={
                        "path": path,
                        "content": content,
                        "size_bytes": len(content.encode('utf-8'))
                    }
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    result=None,
                    error=str(e)
                )


class WriteFileTool(BaseTool):
    """Write content to a file"""
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Create or update a file with the specified content"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file relative to workspace root"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    
    @property
    def category(self) -> str:
        return "file_operations"
    
    @property
    def requires_confirmation(self) -> bool:
        return True
    
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        path = args.get("path", "")
        content = args.get("content", "")
        
        if not path:
            return ToolResult(
                success=False,
                result=None,
                error="No path provided"
            )
        
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write file (try async first, fallback to sync)
            try:
                import aiofiles
                async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            except:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return ToolResult(
                success=True,
                result={
                    "path": path,
                    "content_length": len(content),
                    "bytes_written": len(content.encode('utf-8'))
                }
            )
        except PermissionError:
            return ToolResult(
                success=False,
                result=None,
                error=f"Permission denied: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )


class ListDirectoryTool(BaseTool):
    """List directory contents"""
    
    @property
    def name(self) -> str:
        return "list_directory"
    
    @property
    def description(self) -> str:
        return "List files and folders in a directory"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to workspace root",
                    "default": "."
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively",
                    "default": False
                }
            }
        }
    
    @property
    def category(self) -> str:
        return "file_operations"
    
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        path = args.get("path", ".")
        recursive = args.get("recursive", False)
        
        try:
            if not os.path.exists(path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path does not exist: {path}"
                )
            
            entries = []
            
            if recursive:
                # Recursive listing
                for root, dirs, files in os.walk(path):
                    for name in dirs:
                        full_path = os.path.join(root, name)
                        rel_path = os.path.relpath(full_path, path)
                        entries.append({
                            "name": rel_path,
                            "type": "directory",
                            "path": full_path
                        })
                    for name in files:
                        full_path = os.path.join(root, name)
                        rel_path = os.path.relpath(full_path, path)
                        try:
                            size = os.path.getsize(full_path)
                        except:
                            size = 0
                        entries.append({
                            "name": rel_path,
                            "type": "file",
                            "path": full_path,
                            "size_bytes": size
                        })
            else:
                # Non-recursive listing
                for entry in os.listdir(path):
                    full_path = os.path.join(path, entry)
                    is_dir = os.path.isdir(full_path)
                    entry_data = {
                        "name": entry,
                        "type": "directory" if is_dir else "file",
                        "path": full_path
                    }
                    if not is_dir:
                        try:
                            entry_data["size_bytes"] = os.path.getsize(full_path)
                        except:
                            entry_data["size_bytes"] = 0
                    entries.append(entry_data)
            
            return ToolResult(
                success=True,
                result={
                    "path": path,
                    "recursive": recursive,
                    "entries": entries,
                    "count": len(entries)
                }
            )
        except PermissionError:
            return ToolResult(
                success=False,
                result=None,
                error=f"Permission denied: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )


class ExecuteCommandTool(BaseTool):
    """Execute CLI commands (Windows/Unix compatible)"""
    
    def __init__(self, working_directory: Optional[str] = None, timeout: int = 60):
        self._working_directory = working_directory
        self._timeout = timeout
    
    @property
    def name(self) -> str:
        return "execute_command"
    
    @property
    def description(self) -> str:
        return "Execute a shell command and return the output. Works on Windows and Unix systems."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute"
                },
                "working_directory": {
                    "type": "string",
                    "description": "Working directory for the command (optional)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 60)",
                    "default": 60
                }
            },
            "required": ["command"]
        }
    
    @property
    def category(self) -> str:
        return "system"
    
    @property
    def requires_confirmation(self) -> bool:
        return True
    
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        command = args.get("command", "")
        working_dir = args.get("working_directory", self._working_directory)
        timeout = args.get("timeout", self._timeout)
        
        if not command:
            return ToolResult(
                success=False,
                result=None,
                error="No command provided"
            )
        
        try:
            # Determine shell based on OS
            is_windows = sys.platform == "win32"
            
            if is_windows:
                # Check if command explicitly starts with powershell
                if command.strip().lower().startswith(('powershell', 'pwsh')):
                    # Execute PowerShell directly to avoid cmd.exe quoting issues
                    shell_cmd = ["powershell", "-NoProfile", "-Command", command.strip().split(None, 2)[2] if len(command.strip().split(None, 2)) > 2 else ""]
                else:
                    # Use cmd.exe for other commands
                    shell_cmd = ["cmd", "/c", command]
            else:
                # Use bash on Unix
                shell_cmd = ["/bin/bash", "-c", command]
            
            # Run command asynchronously
            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return ToolResult(
                    success=process.returncode == 0,
                    result={
                        "command": command,
                        "return_code": process.returncode,
                        "stdout": stdout.decode("utf-8", errors="replace"),
                        "stderr": stderr.decode("utf-8", errors="replace"),
                        "working_directory": working_dir
                    },
                    error=None if process.returncode == 0 else f"Command exited with code {process.returncode}"
                )
                
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    result={"command": command},
                    error=f"Command timed out after {timeout} seconds"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                result={"command": command},
                error=str(e)
            )


class FindRecentsTool(BaseTool):
    """Find recently modified files"""
    
    @property
    def name(self) -> str:
        return "find_recents"
    
    @property
    def description(self) -> str:
        return "Find recently modified files in the workspace"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back",
                    "default": 7
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of files to return",
                    "default": 20
                }
            }
        }
    
    @property
    def category(self) -> str:
        return "file_operations"
    
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        days = args.get("days", 7)
        limit = args.get("limit", 20)
        return ToolResult(
            success=True,
            result={
                "days": days,
                "limit": limit,
                "files": [],
                "status": "delegated_to_core"
            }
        )


class CreateDirectoryTool(BaseTool):
    """Create a directory"""
    
    @property
    def name(self) -> str:
        return "create_directory"
    
    @property
    def description(self) -> str:
        return "Create a new directory at the specified path"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to create"
                }
            },
            "required": ["path"]
        }
    
    @property
    def category(self) -> str:
        return "file_operations"
    
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        path = args.get("path", "")
        
        if not path:
            return ToolResult(
                success=False,
                result=None,
                error="No path provided"
            )
        
        try:
            os.makedirs(path, exist_ok=True)
            return ToolResult(
                success=True,
                result={
                    "path": path,
                    "created": True
                }
            )
        except PermissionError:
            return ToolResult(
                success=False,
                result=None,
                error=f"Permission denied: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )


class DeleteFileTool(BaseTool):
    """Delete a file"""
    
    @property
    def name(self) -> str:
        return "delete_file"
    
    @property
    def description(self) -> str:
        return "Delete a file at the specified path"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to delete"
                }
            },
            "required": ["path"]
        }
    
    @property
    def category(self) -> str:
        return "file_operations"
    
    @property
    def requires_confirmation(self) -> bool:
        return True
    
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        path = args.get("path", "")
        
        if not path:
            return ToolResult(
                success=False,
                result=None,
                error="No path provided"
            )
        
        try:
            if not os.path.exists(path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"File does not exist: {path}"
                )
            
            if os.path.isdir(path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path is a directory, not a file: {path}"
                )
            
            os.remove(path)
            return ToolResult(
                success=True,
                result={
                    "path": path,
                    "deleted": True
                }
            )
        except PermissionError:
            return ToolResult(
                success=False,
                result=None,
                error=f"Permission denied: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )


class ToolRegistry:
    """Central registry for all tools - easily extensible"""
    
    def __init__(self, working_directory: Optional[str] = None):
        self._tools: Dict[str, BaseTool] = {}
        self._working_directory = working_directory
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register built-in tools"""
        default_tools = [
            SearchTool(),
            ReadFileTool(),
            WriteFileTool(),
            ListDirectoryTool(),
            ExecuteCommandTool(working_directory=self._working_directory),
            FindRecentsTool(),
            CreateDirectoryTool(),
            DeleteFileTool(),
        ]
        for tool in default_tools:
            self.register(tool)
    
    def register(self, tool: BaseTool) -> None:
        """Register a new tool"""
        self._tools[tool.name] = tool
    
    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools"""
        return [tool.to_definition() for tool in self._tools.values()]
    
    def list_by_category(self, category: str) -> List[ToolDefinition]:
        """List tools by category"""
        return [
            tool.to_definition() 
            for tool in self._tools.values() 
            if tool.category == category
        ]
    
    def get_categories(self) -> List[str]:
        """Get all tool categories"""
        return list(set(tool.category for tool in self._tools.values()))


class ToolExecutor:
    """Executes tools and returns results"""
    
    def __init__(self, working_directory: Optional[str] = None):
        self._working_directory = working_directory
        self.registry = ToolRegistry(working_directory=working_directory)
    
    def _resolve_path(self, path: str) -> str:
        """Resolve a path relative to working directory"""
        if not path:
            return path
        if os.path.isabs(path):
            return path
        if self._working_directory:
            return os.path.join(self._working_directory, path)
        return path
    
    async def execute(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute a tool with given arguments"""
        start_time = time.time()
        
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                error=f"Unknown tool: {tool_name}. Available: {[t.name for t in self.registry.list_tools()]}"
            )
        
        # Resolve paths in arguments relative to working directory
        # Handle multiple path argument names used by different tools
        resolved_args = dict(arguments)
        path_arg_names = ['path', 'source_path', 'destination_path', 'file_path', 'directory']
        
        if self._working_directory:
            for arg_name in path_arg_names:
                if arg_name in resolved_args:
                    resolved_args[arg_name] = self._resolve_path(resolved_args[arg_name])
            
            # Default working directory for execute_command
            if tool_name == 'execute_command' and 'working_directory' not in resolved_args:
                resolved_args['working_directory'] = self._working_directory
        
        try:
            result = await tool.execute(resolved_args)
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of available tools"""
        return {tool.name: tool.description for tool in self.registry.list_tools()}
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get JSON schemas for all tools (for function calling)"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.registry.list_tools()
        ]
