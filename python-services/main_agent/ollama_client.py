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
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma:7b")
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
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("message", {}).get("content", "")
                    
                    # Parse for tool calls (simple pattern matching)
                    tool_calls = self._parse_tool_calls(content, tools or [])
                    
                    return content, tool_calls
                else:
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
        Looks for patterns like: [TOOL: search("query")]
        """
        tool_calls = []
        
        # Pattern for tool calls
        patterns = [
            r'\[TOOL:\s*(\w+)\s*\((.*?)\)\]',
            r'<tool>(\w+)\((.*?)\)</tool>',
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
