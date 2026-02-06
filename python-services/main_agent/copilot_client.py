"""
Copilot Client
Handles communication with GitHub Copilot CLI as a persistent HTTP-accessible chat service
"""

import asyncio
import json
import re
import os
from typing import List, Dict, Any, Optional, Tuple
import subprocess


class CopilotClient:
    """Client for GitHub Copilot CLI that maintains a persistent session"""
    
    def __init__(self):
        self.process = None
        self.session_active = False
        self.lock = asyncio.Lock()  # Ensure thread-safe access to the process
        self.timeout = 120.0
        self.response_buffer = []
        
    async def _ensure_session(self) -> bool:
        """Ensure Copilot CLI session is active, start if needed"""
        async with self.lock:
            if self.process is not None and self.process.poll() is None:
                return True
            
            # Check if gh copilot is available
            try:
                check_result = subprocess.run(
                    ["gh", "copilot", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if check_result.returncode != 0:
                    print("[COPILOT] GitHub Copilot CLI not available")
                    return False
            except Exception as e:
                print(f"[COPILOT] Error checking Copilot availability: {e}")
                return False
            
            # Start interactive Copilot session
            try:
                # Use gh copilot suggest with interactive mode
                self.process = subprocess.Popen(
                    ["gh", "copilot", "suggest", "-t", "shell"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                self.session_active = True
                print("[COPILOT] Started persistent Copilot CLI session")
                return True
                
            except Exception as e:
                print(f"[COPILOT] Failed to start Copilot session: {e}")
                self.session_active = False
                return False
    
    async def check_model(self) -> bool:
        """Check if Copilot CLI is available and authenticated"""
        try:
            # Check auth status
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print("[COPILOT] Not authenticated with GitHub")
                return False
            
            # Check Copilot availability
            result = subprocess.run(
                ["gh", "copilot", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"[COPILOT] Health check failed: {e}")
            return False
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        tools: List[str] = None
    ) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
        """
        Send chat messages to Copilot CLI and get response
        Returns tuple of (response_text, tool_calls)
        """
        try:
            # Build prompt from messages
            prompt = self._messages_to_prompt(messages, tools)
            
            # Use gh copilot suggest for each query (stateless approach)
            # This is more reliable than trying to maintain interactive session
            result = subprocess.run(
                ["gh", "copilot", "suggest", prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                
                # Clean up the response (Copilot adds formatting)
                response = self._clean_copilot_response(response)
                
                # Parse for tool calls if tools are available
                tool_calls = self._parse_tool_calls(response, tools or [])
                
                return response, tool_calls
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"[COPILOT] Error: {error_msg}")
                return f"Error: {error_msg}", None
                
        except subprocess.TimeoutExpired:
            return "Error: Request timed out. Copilot CLI took too long to respond.", None
        except FileNotFoundError:
            return "Error: GitHub Copilot CLI (gh copilot) not found. Please install it with 'gh extension install github/gh-copilot'", None
        except Exception as e:
            print(f"[COPILOT] Exception: {e}")
            return f"Error: {str(e)}", None
    
    async def complete(self, prompt: str) -> str:
        """Simple text completion"""
        try:
            result = subprocess.run(
                ["gh", "copilot", "suggest", prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                return self._clean_copilot_response(result.stdout.strip())
            else:
                return f"Error: {result.stderr.strip() if result.stderr else 'Unknown error'}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]], tools: List[str] = None) -> str:
        """Convert chat messages into a prompt for Copilot CLI"""
        lines = []
        
        for message in messages:
            role = message.get("role", "user").strip().lower()
            content = message.get("content", "")
            
            if role == "system":
                # System messages provide context
                lines.append(f"Context: {content}")
            elif role == "assistant":
                lines.append(f"Previous response: {content}")
            else:  # user
                lines.append(content)
        
        # If tools are available, add context about them
        if tools:
            lines.insert(0, f"Available tools: {', '.join(tools)}. You can suggest using these tools in your response.")
        
        return "\n".join(lines)
    
    def _clean_copilot_response(self, response: str) -> str:
        """Clean up Copilot CLI response formatting"""
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        response = ansi_escape.sub('', response)
        
        # Remove Copilot CLI formatting markers
        response = response.replace("Suggestion:", "").strip()
        response = response.replace("Explanation:", "\n\nExplanation:").strip()
        
        # Remove excessive newlines
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        return response.strip()
    
    def _parse_tool_calls(
        self, 
        content: str, 
        available_tools: List[str]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Parse response content for tool calls
        Copilot may suggest commands that map to our tools
        """
        tool_calls = []
        
        # Try to parse JSON format first (if Copilot returns structured data)
        json_patterns = [
            r'```json\s*\n?({[\s\S]*?})\s*\n?```',
            r'```\s*\n?({[\s\S]*?"tool_calls"[\s\S]*?})\s*\n?```',
            r'({[\s\S]*?"tool_calls"[\s\S]*?})',
        ]
        
        for pattern in json_patterns:
            json_matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for json_str in json_matches:
                try:
                    data = json.loads(json_str)
                    if isinstance(data, dict) and "tool_calls" in data:
                        calls = data["tool_calls"]
                        if isinstance(calls, list):
                            for call in calls:
                                if isinstance(call, dict) and "name" in call and "arguments" in call:
                                    tool_name = call["name"]
                                    if tool_name.lower() in [t.lower() for t in available_tools]:
                                        tool_calls.append({
                                            "name": tool_name.lower(),
                                            "arguments": call["arguments"]
                                        })
                except json.JSONDecodeError:
                    continue
            
            if tool_calls:
                break
        
        # Map common Copilot command suggestions to our tools
        if not tool_calls:
            tool_calls = self._map_copilot_commands_to_tools(content, available_tools)
        
        return tool_calls if tool_calls else None
    
    def _map_copilot_commands_to_tools(
        self, 
        content: str, 
        available_tools: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Map Copilot's suggested shell commands to our tool system
        E.g., 'cat file.txt' -> read_file tool
        """
        tool_calls = []
        
        # Look for common command patterns in code blocks
        code_block_pattern = r'```(?:bash|sh|shell)?\s*\n(.*?)\n```'
        code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
        
        for command in code_blocks:
            command = command.strip()
            
            # Map cat/type commands to read_file
            if "read_file" in available_tools:
                cat_match = re.match(r'(?:cat|type)\s+["\']?(.+?)["\']?\s*$', command)
                if cat_match:
                    file_path = cat_match.group(1)
                    tool_calls.append({
                        "name": "read_file",
                        "arguments": {"path": file_path}
                    })
                    continue
            
            # Map ls/dir commands to list_directory
            if "list_directory" in available_tools:
                ls_match = re.match(r'(?:ls|dir)(?:\s+["\']?(.+?)["\']?)?\s*$', command)
                if ls_match:
                    dir_path = ls_match.group(1) if ls_match.group(1) else "."
                    tool_calls.append({
                        "name": "list_directory",
                        "arguments": {"path": dir_path}
                    })
                    continue
            
            # Map grep/findstr to search
            if "search" in available_tools:
                grep_match = re.match(r'(?:grep|findstr)\s+["\'](.+?)["\']\s+(.+)$', command)
                if grep_match:
                    query = grep_match.group(1)
                    tool_calls.append({
                        "name": "search",
                        "arguments": {"query": query}
                    })
                    continue
            
            # For other commands, suggest execute_command if available
            if "execute_command" in available_tools and command:
                tool_calls.append({
                    "name": "execute_command",
                    "arguments": {"command": command}
                })
        
        return tool_calls
    
    async def close(self):
        """Close the Copilot session"""
        async with self.lock:
            if self.process is not None:
                try:
                    self.process.terminate()
                    await asyncio.sleep(0.5)
                    if self.process.poll() is None:
                        self.process.kill()
                    print("[COPILOT] Closed Copilot CLI session")
                except Exception as e:
                    print(f"[COPILOT] Error closing session: {e}")
                finally:
                    self.process = None
                    self.session_active = False
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.process is not None:
            try:
                self.process.terminate()
            except:
                pass
