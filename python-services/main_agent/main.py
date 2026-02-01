"""
Main Agent Service
Handles chat interactions with local Ollama models (Gemma)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from datetime import datetime
import uuid

from ollama_client import OllamaClient
from tool_logic import ToolExecutor

app = FastAPI(
    title="Main Agent Service",
    description="Chat agent service using local Ollama models",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
ollama_client = OllamaClient(model="glm-4.6:cloud")
# OllamaClient(model="qwen3-vl:235b-cloud")
tool_executor = ToolExecutor()


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    tools: List[str] = []
    project_id: Optional[str] = None


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ChatResponse(BaseModel):
    response: str
    tool_calls: Optional[List[ToolCall]] = None
    message_id: str


class HealthResponse(BaseModel):
    status: str
    model_available: bool
    ollama_url: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and model availability"""
    model_available = await ollama_client.check_model()
    return HealthResponse(
        status="healthy" if model_available else "degraded",
        model_available=model_available,
        ollama_url=ollama_client.base_url
    )


@app.post("/agent/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat message with optional tool usage
    """
    try:
        # Build system prompt with tools
        system_prompt = build_system_prompt(request.tools)
        
        # Build messages
        messages = []
        if request.context:
            messages.append({
                "role": "system",
                "content": f"{system_prompt}\n\nContext:\n{request.context}"
            })
        else:
            messages.append({
                "role": "system", 
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Get response from Ollama
        response_text, tool_calls = await ollama_client.chat(messages, request.tools)
        
        return ChatResponse(
            response=response_text,
            tool_calls=[ToolCall(name=tc["name"], arguments=tc["arguments"]) for tc in tool_calls] if tool_calls else None,
            message_id=str(uuid.uuid4())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/complete")
async def complete(prompt: str):
    """Simple completion without tool usage"""
    try:
        response = await ollama_client.complete(prompt)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/shutdown")
async def shutdown():
    """Graceful shutdown endpoint"""
    return {"status": "shutting_down"}


def build_system_prompt(tools: List[str]) -> str:
    """Build system prompt with available tools"""
    base_prompt = """You are a helpful AI workspace assistant. You help users organize their notes, research, and code files.
You have access to a workspace where you can search, read, and write files.
Always be helpful, concise, and accurate. When you need information from the workspace, use the available tools."""

    if tools:
        tool_descriptions = []
        for tool in tools:
            if tool == "search":
                tool_descriptions.append("- search(query): Search the workspace for relevant content")
            elif tool == "read_file":
                tool_descriptions.append("- read_file(path): Read the contents of a file")
            elif tool == "write_file":
                tool_descriptions.append("- write_file(path, content): Create or update a file")
        
        if tool_descriptions:
            base_prompt += "\n\nAvailable tools:\n" + "\n".join(tool_descriptions)
    
    return base_prompt


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
