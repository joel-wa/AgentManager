"""
Ollama Client
Handles communication with the local Ollama server
"""

import httpx
from typing import List, Dict, Any, Optional, Tuple
import json
import re
import os


class OllamaClient:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "kimi-k2.5:cloud")
        self.timeout = 120.0  # Longer timeout for model inference
    
    async def check_model(self) -> bool:
        """Check if the model is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return any(self.model in m for m in models)
                return False
        except Exception:
            return False
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        tools: List[str] = None
    ) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
        """
        Send chat messages to Ollama and get response
        Returns tuple of (response_text, tool_calls)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                        }
                    },
                    timeout=self.timeout
                )

                if response.status_code == 404:
                    prompt = self._messages_to_prompt(messages)
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9,
                            }
                        },
                        timeout=self.timeout
                    )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("message", {}).get("content") or data.get("response", "")

                    # Parse for tool calls (simple pattern matching)
                    tool_calls = self._parse_tool_calls(content, tools or [])

                    return content, tool_calls

                error_detail = self._extract_error(response)
                if error_detail:
                    return f"Error: {error_detail}", None

                return f"Error: Unable to get response from Ollama ({response.status_code})", None

        except httpx.TimeoutException:
            return "Error: Request timed out. The model might be loading or busy.", None
        except httpx.ConnectError:
            return "Error: Cannot connect to Ollama. Please ensure Ollama is running.", None
        except Exception as e:
            return f"Error: {str(e)}", None
    
    async def complete(self, prompt: str) -> str:
        """Simple text completion"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                return f"Error: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _parse_tool_calls(
        self, 
        content: str, 
        available_tools: List[str]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Parse response content for tool calls
        Supports multiple formats:
        1. JSON format: ```json{"tool_calls": [...]}```
        2. Legacy patterns: [TOOL: search("query")], <tool>search("query")</tool>
        """
        tool_calls = []
        
        # First, try to parse JSON format (preferred)
        json_pattern = r'```json\s*\n?({[\s\S]*?})\s*\n?```'
        json_matches = re.findall(json_pattern, content, re.IGNORECASE | re.MULTILINE)
        
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
                pass  # Try legacy patterns
        
        # If JSON parsing succeeded, return those calls
        if tool_calls:
            return tool_calls
        
        # Fall back to legacy text patterns
        patterns = [
            r'\[TOOL:\s*(\w+)\s*\((.*?)\)\]',
            r'<tool>(\w+)\((.*?)</tool>',
            r'\*\*Tool:\*\*\s*(\w+)\s*\((.*?)\)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                tool_name, args_str = match
                if tool_name.lower() in [t.lower() for t in available_tools]:
                    # Parse arguments
                    args = self._parse_args(args_str)
                    tool_calls.append({
                        "name": tool_name.lower(),
                        "arguments": args
                    })
        
        return tool_calls if tool_calls else None

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages into a single prompt for /api/generate"""
        lines = []
        for message in messages:
            role = message.get("role", "user").strip().lower()
            content = message.get("content", "")
            if role == "system":
                lines.append(f"System: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            else:
                lines.append(f"User: {content}")
        lines.append("Assistant:")
        return "\n".join(lines)

    def _extract_error(self, response: httpx.Response) -> Optional[str]:
        """Extract error details from an Ollama response if available"""
        try:
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                return data.get("error")
        except Exception:
            return None
        return None
    
    def _parse_args(self, args_str: str) -> Dict[str, Any]:
        """Parse tool arguments from string"""
        args = {}
        
        # Try to parse as JSON first
        try:
            if args_str.strip().startswith('{'):
                return json.loads(args_str)
        except json.JSONDecodeError:
            pass
        
        # Simple parsing for quoted strings
        # e.g., "query", path="file.md"
        parts = args_str.split(',')
        
        for i, part in enumerate(parts):
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                args[key.strip()] = self._clean_value(value)
            elif part:
                # Positional argument
                if i == 0:
                    args["query"] = self._clean_value(part)
                elif i == 1:
                    args["path"] = self._clean_value(part)
        
        return args
    
    def _clean_value(self, value: str) -> str:
        """Clean quoted value"""
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        return value
