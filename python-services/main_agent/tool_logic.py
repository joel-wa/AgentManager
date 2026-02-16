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
import shutil
import re
from pathlib import Path


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class VenvManager:
    """Manages temporary virtual environments per project/session"""
    
    def __init__(self, venv_base_dir: Optional[str] = None):
        """Initialize venv manager
        
        Args:
            venv_base_dir: Base directory for storing venvs. 
                          Defaults to ~/.agent-workspace/venvs
        """
        if venv_base_dir:
            self.venv_base_dir = Path(venv_base_dir)
        else:
            # Use user home directory for venvs
            home = Path.home()
            self.venv_base_dir = home / '.agent-workspace' / 'venvs'
        
        # Ensure base directory exists
        self.venv_base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_venv_path(self, project_id: str) -> Path:
        """Get the venv path for a specific project"""
        return self.venv_base_dir / project_id
    
    def venv_exists(self, project_id: str) -> bool:
        """Check if venv exists for a project"""
        venv_path = self.get_venv_path(project_id)
        
        # Check for key venv markers
        if sys.platform == "win32":
            python_exe = venv_path / 'Scripts' / 'python.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
        
        return python_exe.exists()
    
    async def create_venv(self, project_id: str) -> tuple[bool, str]:
        """Create a new venv for a project
        
        Returns:
            (success, message) tuple
        """
        venv_path = self.get_venv_path(project_id)
        
        if self.venv_exists(project_id):
            return True, f"Venv already exists at {venv_path}"
        
        try:
            print(f"[VENV] Creating venv for project {project_id} at {venv_path}")
            
            # Create venv using current Python interpreter
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'venv', str(venv_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                return False, f"Failed to create venv: {error_msg}"
            
            print(f"[VENV] Successfully created venv at {venv_path}")
            return True, f"Created venv at {venv_path}"
            
        except asyncio.TimeoutError:
            return False, "Venv creation timed out"
        except Exception as e:
            return False, f"Error creating venv: {str(e)}"
    
    def get_python_executable(self, project_id: str) -> Optional[str]:
        """Get the Python executable path for a project's venv"""
        if not self.venv_exists(project_id):
            return None
        
        venv_path = self.get_venv_path(project_id)
        
        if sys.platform == "win32":
            python_exe = venv_path / 'Scripts' / 'python.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
        
        return str(python_exe) if python_exe.exists() else None
    
    def get_pip_executable(self, project_id: str) -> Optional[str]:
        """Get the pip executable path for a project's venv"""
        if not self.venv_exists(project_id):
            return None
        
        venv_path = self.get_venv_path(project_id)
        
        if sys.platform == "win32":
            pip_exe = venv_path / 'Scripts' / 'pip.exe'
        else:
            pip_exe = venv_path / 'bin' / 'pip'
        
        return str(pip_exe) if pip_exe.exists() else None
    
    def delete_venv(self, project_id: str) -> tuple[bool, str]:
        """Delete a project's venv
        
        Returns:
            (success, message) tuple
        """
        venv_path = self.get_venv_path(project_id)
        
        if not venv_path.exists():
            return True, "Venv does not exist"
        
        try:
            shutil.rmtree(venv_path)
            return True, f"Deleted venv at {venv_path}"
        except Exception as e:
            return False, f"Error deleting venv: {str(e)}"


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
        working_directory = args.get("_working_directory", ".")
        
        if not query:
            return ToolResult(
                success=False,
                result=None,
                error="No search query provided"
            )
        
        try:
            matches = []
            query_lower = query.lower()
            
            # Directories to ignore
            ignore_dirs = {'.git', '__pycache__', 'node_modules', 'target', 'dist', 
                          'build', '.venv', 'venv', '.cache', '.pytest_cache'}
            
            # File extensions to search (text files and PDFs)
            text_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.md', '.txt', 
                             '.json', '.yaml', '.yml', '.toml', '.rs', '.go', 
                             '.java', '.cpp', '.c', '.h', '.hpp', '.html', '.css',
                             '.sql', '.sh', '.bat', '.ps1', '.xml', '.ini', '.conf', '.pdf'}
            
            # Walk through directory
            for root, dirs, files in os.walk(working_directory):
                # Remove ignored directories from search
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                
                # Check if we have enough results
                if len(matches) >= max_results:
                    break
                
                for filename in files:
                    if len(matches) >= max_results:
                        break
                    
                    # Check file extension
                    _, ext = os.path.splitext(filename)
                    if ext not in text_extensions:
                        continue
                    
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, working_directory)
                    
                    try:
                        # Handle PDF files differently
                        if ext == '.pdf':
                            try:
                                from pypdf import PdfReader
                                reader = PdfReader(filepath)
                                for page_num, page in enumerate(reader.pages, 1):
                                    try:
                                        page_text = page.extract_text()
                                        if query_lower in page_text.lower():
                                            # Find the line containing the query
                                            for line_num, line in enumerate(page_text.split('\n'), 1):
                                                if query_lower in line.lower():
                                                    matches.append({
                                                        "file": rel_path,
                                                        "line": f"page {page_num}, line {line_num}",
                                                        "content": line.strip()[:200],
                                                        "relevance": 1.0
                                                    })
                                                    
                                                    if len(matches) >= max_results:
                                                        break
                                    except:
                                        continue
                                    
                                    if len(matches) >= max_results:
                                        break
                            except ImportError:
                                # pypdf not installed, skip PDF files
                                continue
                            except:
                                # Skip problematic PDFs
                                continue
                        else:
                            # Read text file and search for query
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_num, line in enumerate(f, 1):
                                    if query_lower in line.lower():
                                        matches.append({
                                            "file": rel_path,
                                            "line": line_num,
                                            "content": line.strip()[:200],  # Limit line length
                                            "relevance": 1.0  # Simple grep doesn't score relevance
                                        })
                                        
                                        if len(matches) >= max_results:
                                            break
                    except (PermissionError, UnicodeDecodeError, IsADirectoryError):
                        # Skip files we can't read
                        continue
            
            return ToolResult(
                success=True,
                result={
                    "query": query,
                    "max_results": max_results,
                    "matches": matches,
                    "total_found": len(matches)
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Search failed: {str(e)}"
            )


class ReadFileTool(BaseTool):
    """Read file contents (supports text files and PDFs)"""
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read the contents of a file at the specified path (supports text files and PDFs)"
    
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
        
        # Check if file is a PDF
        is_pdf = path.lower().endswith('.pdf')
        
        try:
            if is_pdf:
                # Extract text from PDF
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(path)
                    text_content = []
                    
                    for page_num, page in enumerate(reader.pages, 1):
                        try:
                            page_text = page.extract_text()
                            if page_text.strip():
                                text_content.append(f"--- Page {page_num} ---\n{page_text}")
                        except Exception as e:
                            text_content.append(f"--- Page {page_num} ---\n[Error extracting text: {str(e)}]")
                    
                    content = "\n\n".join(text_content)
                    
                    return ToolResult(
                        success=True,
                        result={
                            "path": path,
                            "content": content,
                            "size_bytes": len(content.encode('utf-8')),
                            "file_type": "pdf",
                            "pages": len(reader.pages)
                        }
                    )
                except ImportError:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="PDF support not available. Install pypdf: pip install pypdf"
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        result=None,
                        error=f"Failed to read PDF: {str(e)}"
                    )
            else:
                # Read text file asynchronously
                try:
                    import aiofiles
                    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                except:
                    # Fallback to sync read
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                return ToolResult(
                    success=True,
                    result={
                        "path": path,
                        "content": content,
                        "size_bytes": len(content.encode('utf-8')),
                        "file_type": "text"
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
        project_id = args.get("_project_id")
        rust_core_url = args.get("_rust_core_url", "http://localhost:8000")
        working_directory = args.get("_working_directory")
        
        if not path:
            return ToolResult(
                success=False,
                result=None,
                error="No path provided"
            )
        
        # If we have a project_id, use Rust Core API for version tracking
        if project_id and working_directory:
            try:
                # Calculate relative path from working directory
                abs_path = path if os.path.isabs(path) else path
                if os.path.isabs(abs_path) and working_directory:
                    # Make path relative to project root
                    rel_path = os.path.relpath(abs_path, working_directory)
                else:
                    rel_path = path
                
                # Call Rust Core API
                import httpx
                from urllib.parse import quote
                
                api_url = f"{rust_core_url}/api/projects/{project_id}/files/{quote(rel_path, safe='')}"
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        api_url,
                        content=content,
                        headers={"Content-Type": "text/plain"}
                    )
                    
                    if response.status_code == 200:
                        return ToolResult(
                            success=True,
                            result={
                                "path": rel_path,
                                "content_length": len(content),
                                "bytes_written": len(content.encode('utf-8')),
                                "version_tracked": True
                            }
                        )
                    else:
                        return ToolResult(
                            success=False,
                            result=None,
                            error=f"API error: {response.status_code} - {response.text}"
                        )
            except Exception as e:
                # Fall back to direct file write if API fails
                print(f"[WRITE_FILE] API call failed, falling back to direct write: {e}")
        
        # Fallback: Direct file write (no version tracking)
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
                    "bytes_written": len(content.encode('utf-8')),
                    "version_tracked": False
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
    """Execute CLI commands (Windows/Unix compatible) with automatic venv support"""
    
    def __init__(self, working_directory: Optional[str] = None, timeout: int = 60, project_id: Optional[str] = None):
        self._working_directory = working_directory
        self._timeout = timeout
        self._project_id = project_id
        self._venv_manager = VenvManager() if project_id else None
    
    @property
    def name(self) -> str:
        return "execute_command"
    
    @property
    def description(self) -> str:
        return "Execute a shell command and return the output. Works on Windows and Unix systems. Python/pip commands automatically use project-specific venv."
    
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
    
    async def _ensure_venv(self) -> tuple[bool, Optional[str]]:
        """Ensure venv exists for this project
        
        Returns:
            (success, error_message) tuple
        """
        if not self._project_id or not self._venv_manager:
            return True, None
        
        if not self._venv_manager.venv_exists(self._project_id):
            print(f"[VENV] Venv does not exist for project {self._project_id}, creating...")
            success, message = await self._venv_manager.create_venv(self._project_id)
            if not success:
                return False, message
            print(f"[VENV] {message}")
        
        return True, None
    
    def _transform_command_for_venv(self, command: str) -> str:
        """Transform Python/pip commands to use project venv
        
        Handles multiple command patterns:
        - python, python3, python2, py
        - pip, pip3, pip2
        - python -m pip
        - Full paths like C:\\Python311\\python.exe
        - py -3.11 -m pip
        
        Args:
            command: Original command string
            
        Returns:
            Transformed command that uses venv executables
        """
        if not self._project_id or not self._venv_manager:
            return command
        
        command_stripped = command.strip()
        
        # Pattern 1: Direct pip commands (pip, pip3, pip2, pip.exe, etc.)
        # Matches: pip install, pip3 install, pip.exe list
        pip_pattern = r'^(pip\d*(?:\.exe)?)\s+'
        pip_match = re.match(pip_pattern, command_stripped, re.IGNORECASE)
        
        if pip_match:
            venv_pip = self._venv_manager.get_pip_executable(self._project_id)
            if venv_pip:
                # Replace pip command with venv pip
                original_pip_cmd = pip_match.group(1)
                rest_of_command = command_stripped[len(original_pip_cmd):].strip()
                transformed = f'"{venv_pip}" {rest_of_command}'
                print(f"[VENV] Transformed '{original_pip_cmd}' to use venv pip")
                return transformed
        
        # Pattern 2: Python commands - direct invocation
        # Matches: python, python3, python.exe, py, py.exe
        # Also matches full paths: C:\Python311\python.exe, /usr/bin/python3
        python_simple_pattern = r'^((?:[a-zA-Z]:[\\\/])?(?:[\w\-\.\\\/]+[\\\/])?(?:python\d*(?:\.exe)?|py(?:\.exe)?))\s+'
        python_match = re.match(python_simple_pattern, command_stripped, re.IGNORECASE)
        
        if python_match:
            venv_python = self._venv_manager.get_python_executable(self._project_id)
            if venv_python:
                original_python_cmd = python_match.group(1)
                rest_of_command = command_stripped[len(original_python_cmd):].strip()
                
                # Special handling for "python -m pip" - use venv pip directly
                if rest_of_command.startswith('-m pip'):
                    venv_pip = self._venv_manager.get_pip_executable(self._project_id)
                    if venv_pip:
                        # Extract what comes after "-m pip"
                        pip_args = rest_of_command[6:].strip()  # Remove "-m pip"
                        transformed = f'"{venv_pip}" {pip_args}'
                        print(f"[VENV] Transformed 'python -m pip' to use venv pip")
                        return transformed
                
                # Regular python command
                transformed = f'"{venv_python}" {rest_of_command}'
                print(f"[VENV] Transformed '{original_python_cmd}' to use venv python")
                return transformed
        
        # Pattern 3: Windows Python Launcher with version specifier
        # Matches: py -3.11, py -3, py -2
        py_version_pattern = r'^py(?:\.exe)?\s+-\d+(?:\.\d+)?\s+'
        py_version_match = re.match(py_version_pattern, command_stripped, re.IGNORECASE)
        
        if py_version_match:
            venv_python = self._venv_manager.get_python_executable(self._project_id)
            if venv_python:
                # Extract everything after the version specifier
                matched_part = py_version_match.group(0)
                rest_of_command = command_stripped[len(matched_part):].strip()
                
                # Check for -m pip pattern
                if rest_of_command.startswith('-m pip'):
                    venv_pip = self._venv_manager.get_pip_executable(self._project_id)
                    if venv_pip:
                        pip_args = rest_of_command[6:].strip()
                        transformed = f'"{venv_pip}" {pip_args}'
                        print(f"[VENV] Transformed 'py -X.X -m pip' to use venv pip")
                        return transformed
                
                # Regular py command
                transformed = f'"{venv_python}" {rest_of_command}'
                print(f"[VENV] Transformed 'py -X.X' to use venv python")
                return transformed
        
        return command
    
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
        
        # Ensure venv exists if this is a project command
        venv_success, venv_error = await self._ensure_venv()
        if not venv_success:
            return ToolResult(
                success=False,
                result=None,
                error=f"Failed to prepare venv: {venv_error}"
            )
        
        # Transform command to use venv if applicable
        original_command = command
        command = self._transform_command_for_venv(command)
        
        start_time = time.time()
        
        try:
            # Determine shell based on OS
            is_windows = sys.platform == "win32"
            
            if is_windows:
                # Use PowerShell for better compatibility and performance
                # PowerShell handles pipes, redirects, and variables natively
                shell_cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command]
            else:
                # Use bash on Unix
                shell_cmd = ["/bin/bash", "-c", command]
            
            # Run command asynchronously with better buffering
            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                creationflags=subprocess.CREATE_NO_WINDOW if is_windows else 0
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                execution_time = (time.time() - start_time) * 1000
                
                # Decode output with better encoding handling
                stdout_text = stdout.decode("utf-8", errors="replace").strip()
                stderr_text = stderr.decode("utf-8", errors="replace").strip()
                
                # Success if return code is 0
                success = process.returncode == 0
                
                return ToolResult(
                    success=success,
                    result={
                        "command": command,
                        "return_code": process.returncode,
                        "stdout": stdout_text,
                        "stderr": stderr_text,
                        "working_directory": working_dir or os.getcwd()
                    },
                    error=stderr_text if not success and stderr_text else None,
                    execution_time_ms=execution_time
                )
                
            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                    
                return ToolResult(
                    success=False,
                    result={"command": command, "working_directory": working_dir},
                    error=f"Command timed out after {timeout} seconds",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
                
        except FileNotFoundError as e:
            return ToolResult(
                success=False,
                result={"command": command},
                error=f"Command not found: {str(e)}",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result={"command": command},
                error=f"Execution error: {str(e)}",
                execution_time_ms=(time.time() - start_time) * 1000
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
        project_id = args.get("_project_id")
        rust_core_url = args.get("_rust_core_url", "http://localhost:8000")
        working_directory = args.get("_working_directory")
        
        if not path:
            return ToolResult(
                success=False,
                result=None,
                error="No path provided"
            )
        
        # If we have a project_id, use Rust Core API for version tracking
        if project_id and working_directory:
            try:
                # Calculate relative path from working directory
                abs_path = path if os.path.isabs(path) else path
                if os.path.isabs(abs_path) and working_directory:
                    # Make path relative to project root
                    rel_path = os.path.relpath(abs_path, working_directory)
                else:
                    rel_path = path
                
                # Call Rust Core API
                import httpx
                from urllib.parse import quote
                
                api_url = f"{rust_core_url}/api/projects/{project_id}/files/{quote(rel_path, safe='')}"
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.delete(api_url)
                    
                    if response.status_code == 200:
                        return ToolResult(
                            success=True,
                            result={
                                "path": rel_path,
                                "deleted": True,
                                "version_tracked": True
                            }
                        )
                    else:
                        return ToolResult(
                            success=False,
                            result=None,
                            error=f"API error: {response.status_code} - {response.text}"
                        )
            except Exception as e:
                # Fall back to direct file delete if API fails
                print(f"[DELETE_FILE] API call failed, falling back to direct delete: {e}")
        
        # Fallback: Direct file delete (no version tracking)
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
                    "deleted": True,
                    "version_tracked": False
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
    
    def __init__(self, working_directory: Optional[str] = None, project_id: Optional[str] = None):
        self._tools: Dict[str, BaseTool] = {}
        self._working_directory = working_directory
        self._project_id = project_id
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register built-in tools"""
        default_tools = [
            SearchTool(),
            ReadFileTool(),
            WriteFileTool(),
            ListDirectoryTool(),
            ExecuteCommandTool(
                working_directory=self._working_directory,
                project_id=self._project_id
            ),
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
    
    def __init__(self, working_directory: Optional[str] = None, project_id: Optional[str] = None, rust_core_url: str = "http://localhost:8000"):
        self._working_directory = working_directory
        self._project_id = project_id
        self._rust_core_url = rust_core_url
        self.registry = ToolRegistry(
            working_directory=working_directory,
            project_id=project_id
        )
    
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
        
        # Inject project_id and rust_core_url for write_file and delete_file tools
        if tool_name in ['write_file', 'delete_file']:
            resolved_args['_project_id'] = self._project_id
            resolved_args['_rust_core_url'] = self._rust_core_url
            resolved_args['_working_directory'] = self._working_directory
        
        # Inject working directory for search tool
        if tool_name == 'search' and self._working_directory:
            resolved_args['_working_directory'] = self._working_directory
        
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
