"""
Gemini Client
Handles communication with the Google Gemini API
"""

import asyncio
import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple


class GeminiClient:
    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY","AIzaSyDwLSJQtKnodLrXobC8Q_D2U9N3-4UJzYs")
        self.base_url = "https://generativelanguage.googleapis.com"
        self.timeout = 120.0
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        try:
            from google import genai
        except ImportError as exc:
            raise ImportError("google-genai is not installed") from exc

        self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def check_model(self) -> bool:
        """Check if Gemini client is configured"""
        try:
            self._get_client()
            return True
        except Exception:
            return False

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[str] = None
    ) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
        """
        Send chat messages to Gemini and get response
        Returns tuple of (response_text, tool_calls)
        """
        try:
            client = self._get_client()
            prompt = self._messages_to_prompt(messages)

            from google.genai import types
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="medium")
                ),
            )

            content = (getattr(response, "text", None) or "").strip()
            if not content:
                content = "Error: Empty response from Gemini"
                return content, None

            tool_calls = self._parse_tool_calls(content, tools or [])
            return content, tool_calls
        except Exception as e:
            return f"Error: {str(e)}", None

    async def complete(self, prompt: str) -> str:
        """Simple text completion"""
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=prompt,
            )
            return (getattr(response, "text", None) or "").strip()
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

        if tool_calls:
            return tool_calls

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
                    args = self._parse_args(args_str)
                    tool_calls.append({
                        "name": tool_name.lower(),
                        "arguments": args
                    })

        return tool_calls if tool_calls else None

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages into a single prompt"""
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

    def _parse_args(self, args_str: str) -> Dict[str, Any]:
        """Parse tool arguments from string"""
        args = {}

        try:
            if args_str.strip().startswith('{'):
                return json.loads(args_str)
        except json.JSONDecodeError:
            pass

        parts = args_str.split(',')

        for i, part in enumerate(parts):
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                args[key.strip()] = self._clean_value(value)
            elif part:
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
