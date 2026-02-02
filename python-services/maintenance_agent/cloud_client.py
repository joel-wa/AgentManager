"""
Cloud Client
Handles communication with cloud AI APIs (Anthropic Claude, OpenAI)
"""

import os
from typing import Optional, Dict, Any, List
import httpx


class CloudClient:
    """Client for cloud AI services"""
    
    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.default_provider = os.getenv("AI_PROVIDER", "anthropic")
        self.timeout = 60.0
    
    async def check_availability(self) -> bool:
        """Check if any cloud API is available"""
        return bool(self.anthropic_key or self.openai_key)
    
    async def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None,
        max_tokens: int = 1024
    ) -> str:
        """Generate text using configured cloud provider"""
        if self.default_provider == "anthropic" and self.anthropic_key:
            return await self._generate_anthropic(prompt, system, max_tokens)
        elif self.openai_key:
            return await self._generate_openai(prompt, system, max_tokens)
        else:
            # Fallback to local response if no API keys
            return self._generate_local_fallback(prompt)
    
    async def _generate_anthropic(
        self, 
        prompt: str, 
        system: Optional[str],
        max_tokens: int
    ) -> str:
        """Generate using Anthropic Claude"""
        try:
            async with httpx.AsyncClient() as client:
                messages = [{"role": "user", "content": prompt}]
                
                payload = {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": max_tokens,
                    "messages": messages
                }
                
                if system:
                    payload["system"] = system
                
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["content"][0]["text"]
                else:
                    return f"Error: {response.status_code}"
                    
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def _generate_openai(
        self, 
        prompt: str, 
        system: Optional[str],
        max_tokens: int
    ) -> str:
        """Generate using OpenAI"""
        try:
            async with httpx.AsyncClient() as client:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": messages,
                        "max_tokens": max_tokens
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"Error: {response.status_code}"
                    
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _generate_local_fallback(self, prompt: str) -> str:
        """Fallback when no cloud APIs available"""
        return "Cloud AI services not configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY."
    
    async def generate_readme(self, context: Dict[str, Any]) -> str:
        """Generate README content for a project"""
        prompt = f"""Generate a README.md for a project with the following details:
        
Project Name: {context.get('name', 'Untitled')}
Description: {context.get('description', 'No description')}
Files: {', '.join(context.get('files', [])[:20])}

Generate a clear, well-structured README with:
1. Project title and description
2. Quick start / Usage
3. File structure overview
4. Any relevant notes

Keep it concise but informative."""

        system = "You are a technical writer creating README documentation. Output only the markdown content, no explanations."
        
        return await self.generate(prompt, system)
    
    async def analyze_for_suggestions(
        self, 
        files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze files for maintenance suggestions"""
        if not files:
            return {"suggestions": []}
        
        files_summary = "\n".join([
            f"- {f.get('name')}: {f.get('summary', 'No summary')}"
            for f in files[:30]
        ])
        
        prompt = f"""Analyze these files for potential improvements:

{files_summary}

Identify:
1. Files that could be merged (similar content)
2. Files that might be outdated
3. Organization improvements

Return a JSON object with 'suggestions' array."""

        system = "You are a workspace organization expert. Return valid JSON only."
        
        response = await self.generate(prompt, system)
        
        # Try to parse JSON, fallback to empty
        try:
            import json
            return json.loads(response)
        except:
            return {"suggestions": []}
