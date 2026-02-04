"""
Main Agent Service
Handles chat interactions with local Ollama models (Gemma)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from datetime import datetime
import uuid
import json
import os
import asyncio
import httpx

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
    workspace_root: Optional[str] = None
    chat_history: Optional[List[Dict[str, str]]] = None


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class ChatResponse(BaseModel):
    response: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None
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
    Implements agentic loop: agent can see tool results and make follow-up decisions
    """
    try:
        # Compute the project working directory
        project_working_dir = None
        if request.workspace_root and request.project_id:
            project_working_dir = os.path.join(
                request.workspace_root, "projects", request.project_id
            )
            # Ensure directory exists
            os.makedirs(project_working_dir, exist_ok=True)
        elif request.workspace_root:
            project_working_dir = request.workspace_root
        
        print(f"[PROJECT] Working directory: {project_working_dir}")
        
        # Create project-specific tool executor
        project_tool_executor = ToolExecutor(working_directory=project_working_dir)
        
        # Get full tool schemas
        tool_schemas = project_tool_executor.get_tool_schemas() if request.tools else []
        
        # Filter to only requested tools
        if request.tools:
            tool_schemas = [t for t in tool_schemas if t["name"] in request.tools]
        
        # Load soul.md if it exists (agent personality/system prompt)
        soul_prompt = ""
        if project_working_dir:
            soul_path = os.path.join(project_working_dir, "soul.md")
            if os.path.exists(soul_path):
                try:
                    with open(soul_path, 'r', encoding='utf-8') as f:
                        soul_prompt = f.read()
                    print(f"[SOUL] Loaded soul.md from {soul_path}")
                except Exception as e:
                    print(f"[SOUL] Error loading soul.md: {e}")
        
        # Build system prompt with tools and soul
        system_prompt = build_system_prompt(tool_schemas, soul_prompt, project_working_dir)
        
        # Build initial messages
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
        
        # Add chat history if provided (last N messages for context)
        if request.chat_history:
            # Limit to last 10 messages for context
            recent_history = request.chat_history[-10:]
            messages.extend(recent_history)
        
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Track user message with maintenance agent
        if request.project_id:
            await track_with_maintenance_agent(
                request.project_id,
                "user",
                request.message
            )
        
        # Agentic loop: allow agent to see results and iterate
        max_iterations = 15  # Increased limit to allow more complex tasks
        all_tool_calls = []
        all_tool_results = []
        final_response = ""
        consecutive_failed_calls = 0  # Track failures to detect when agent is stuck
        
        print(f"\n[AGENTIC LOOP] Starting with max {max_iterations} iterations")
        
        for iteration in range(max_iterations):
            print(f"\n[ITERATION {iteration + 1}] Calling LLM...")
            
            # Get response from Ollama
            response_text, tool_calls = await ollama_client.chat(messages, request.tools)
            final_response = response_text
            
            print(f"[ITERATION {iteration + 1}] Response length: {len(response_text)} chars")
            print(f"[ITERATION {iteration + 1}] Tool calls detected: {len(tool_calls) if tool_calls else 0}")
            
            # If no tool calls, agent is done
            if not tool_calls:
                print(f"[ITERATION {iteration + 1}] No tool calls - agent is done!")
                print(f"[ITERATION {iteration + 1}] Final response: {response_text[:200]}...")
                break
            
            # Execute tools using project-specific executor
            print(f"[ITERATION {iteration + 1}] Executing {len(tool_calls)} tool(s)...")
            iteration_results = []
            iteration_success_count = 0
            
            for tc in tool_calls:
                print(f"  - Executing: {tc['name']}({list(tc['arguments'].keys())})")
                result = await project_tool_executor.execute(tc["name"], tc["arguments"])
                tool_result = ToolResult(
                    tool_name=tc["name"],
                    success=result.success,
                    result=result.result,
                    error=result.error,
                    execution_time_ms=result.execution_time_ms
                )
                iteration_results.append(tool_result)
                all_tool_calls.append(ToolCall(name=tc["name"], arguments=tc["arguments"]))
                all_tool_results.append(tool_result)
                status = "[OK]" if result.success else "[FAIL]"
                print(f"    {status} {tc['name']}: {result.success}")
                
                if result.success:
                    iteration_success_count += 1
            
            # Track consecutive failures to detect if agent is stuck
            if iteration_success_count == 0:
                consecutive_failed_calls += 1
                if consecutive_failed_calls >= 3:
                    print(f"[ITERATION {iteration + 1}] ERROR: Agent stuck with 3 consecutive failed tool calls")
                    # Add error message to help agent understand the situation
                    tool_results_text = "[SYSTEM ERROR]\n"
                    tool_results_text += "You have made 3 consecutive iterations with failed tool calls. "
                    tool_results_text += "Please provide a final answer based on what you know, or explain what information you're missing.\n"
                    tool_results_text += "Do NOT call more tools - provide a natural language response now.\n"
                    
                    messages.append({
                        "role": "user",
                        "content": tool_results_text
                    })
                    
                    # Force one final response from agent
                    print(f"[ITERATION {iteration + 1}] Forcing final response due to stuck state...")
                    response_text, _ = await ollama_client.chat(messages, [])  # No tools allowed
                    final_response = response_text
                    break
            else:
                consecutive_failed_calls = 0
            
            # Add assistant's response to conversation
            messages.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Add tool results as a "user" message so agent can see them
            tool_results_text = "[TOOL RESULTS]\n"
            for tc, tr in zip(tool_calls, iteration_results):
                tool_results_text += f"\n{tc['name']}({json.dumps(tc['arguments'], separators=(',', ':'))}): "
                if tr.success:
                    # Format result based on type
                    if isinstance(tr.result, dict):
                        if 'content' in tr.result:
                            # File content - show full content
                            content = str(tr.result['content'])
                            tool_results_text += f"File read successfully.\nContent:\n{content}\n"
                        elif 'entries' in tr.result:
                            # Directory listing
                            entries = tr.result['entries']
                            tool_results_text += f"Found {len(entries)} items.\n"
                            if entries:
                                tool_results_text += "Items: " + ", ".join([e.get('name', '?') for e in entries[:10]]) + "\n"
                        else:
                            # Generic result
                            tool_results_text += json.dumps(tr.result, indent=2) + "\n"
                    else:
                        tool_results_text += f"{str(tr.result)}\n"
                else:
                    tool_results_text += f"ERROR: {tr.error}\n"
            
            tool_results_text += "\n[END TOOL RESULTS]\nNow provide your answer based on these results. If you need more information, you can call additional tools."
            
            messages.append({
                "role": "user",
                "content": tool_results_text
            })
            
            print(f"[ITERATION {iteration + 1}] Added tool results to conversation. Continuing loop...")
        
        print(f"\n[AGENTIC LOOP] Completed. Total iterations: {iteration + 1}")
        print(f"[AGENTIC LOOP] Total tool calls: {len(all_tool_calls)}")
        print(f"[AGENTIC LOOP] Final response length: {len(final_response)} chars\n")
        
        # Track assistant response with maintenance agent
        if request.project_id and final_response:
            await track_with_maintenance_agent(
                request.project_id,
                "assistant",
                final_response
            )
        
        return ChatResponse(
            response=final_response,
            tool_calls=all_tool_calls if all_tool_calls else None,
            tool_results=all_tool_results if all_tool_results else None,
            message_id=str(uuid.uuid4())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming version of chat endpoint that sends updates as they happen
    Streams tool calls and responses in real-time using Server-Sent Events
    """
    async def event_generator():
        try:
            # Compute the project working directory
            project_working_dir = None
            if request.workspace_root and request.project_id:
                project_working_dir = os.path.join(
                    request.workspace_root, "projects", request.project_id
                )
                os.makedirs(project_working_dir, exist_ok=True)
            elif request.workspace_root:
                project_working_dir = request.workspace_root
            
            # Create project-specific tool executor
            project_tool_executor = ToolExecutor(working_directory=project_working_dir)
            
            # Get full tool schemas
            tool_schemas = project_tool_executor.get_tool_schemas() if request.tools else []
            if request.tools:
                tool_schemas = [t for t in tool_schemas if t["name"] in request.tools]
            
            # Load soul.md
            soul_prompt = ""
            if project_working_dir:
                soul_path = os.path.join(project_working_dir, "soul.md")
                if os.path.exists(soul_path):
                    try:
                        with open(soul_path, 'r', encoding='utf-8') as f:
                            soul_prompt = f.read()
                    except Exception as e:
                        print(f"[SOUL] Error loading soul.md: {e}")
            
            # Build system prompt
            system_prompt = build_system_prompt(tool_schemas, soul_prompt, project_working_dir)
            
            # Build initial messages
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
            
            # Add chat history
            if request.chat_history:
                recent_history = request.chat_history[-10:]
                messages.extend(recent_history)
            
            messages.append({
                "role": "user",
                "content": request.message
            })
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing your request...'})}\n\n"
            
            # Agentic loop with streaming
            max_iterations = 15
            all_tool_calls = []
            final_response = ""
            
            for iteration in range(max_iterations):
                # Send iteration status
                yield f"data: {json.dumps({'type': 'iteration', 'number': iteration + 1})}\n\n"
                
                # Get response from Ollama
                response_text, tool_calls = await ollama_client.chat(messages, request.tools)
                final_response = response_text
                
                # If no tool calls, send final response and finish
                if not tool_calls:
                    yield f"data: {json.dumps({'type': 'response', 'content': response_text})}\n\n"
                    break
                
                # Send tool call notifications and execute tools
                iteration_results = []
                for tc in tool_calls:
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'arguments': tc['arguments']})}\n\n"
                    
                    # Execute tool once
                    result = await project_tool_executor.execute(tc["name"], tc["arguments"])
                    iteration_results.append(result)
                    
                    # Send tool result
                    yield f"data: {json.dumps({'type': 'tool_result', 'name': tc['name'], 'success': result.success, 'preview': str(result.result)[:100]})}\n\n"
                    
                    all_tool_calls.append(ToolCall(name=tc["name"], arguments=tc["arguments"]))
                
                # Add assistant's response to conversation
                messages.append({"role": "assistant", "content": response_text})
                
                # Add tool results
                tool_results_text = "[TOOL RESULTS]\n"
                for tc, result in zip(tool_calls, iteration_results):
                    if result.success:
                        tool_results_text += f"\n{tc['name']}: {str(result.result)}\n"
                    else:
                        tool_results_text += f"\n{tc['name']}: ERROR: {result.error}\n"
                
                messages.append({"role": "user", "content": tool_results_text})
            
            # Send completion
            yield f"data: {json.dumps({'type': 'done', 'message_id': str(uuid.uuid4()), 'tool_calls': len(all_tool_calls)})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


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


@app.get("/agent/tools")
async def list_tools():
    """List all available tools with their schemas"""
    try:
        tools = tool_executor.get_tool_schemas()
        return {
            "tools": tools,
            "count": len(tools)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/execute-tool")
async def execute_tool(tool_name: str, arguments: Dict[str, Any]):
    """Execute a specific tool with given arguments"""
    try:
        result = await tool_executor.execute(tool_name, arguments)
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def build_system_prompt(tool_schemas: List[Dict[str, Any]], soul_prompt: str = "", project_working_dir: str = None) -> str:
    """Build system prompt with available tools, soul prompt, and usage instructions"""
    
    # Start with soul prompt if available (agent personality)
    if soul_prompt:
        base_prompt = soul_prompt.strip() + "\n\n"
    else:
        base_prompt = """You are a helpful AI workspace assistant. You help users organize their notes, research, and code files.
You have access to a workspace where you can search, read, and write files.
Always be helpful, concise, and accurate.

"""
    
    # Add workspace context
    if project_working_dir:
        base_prompt += f"""# WORKSPACE CONTEXT
Your current working directory is: {project_working_dir}
You can use either relative or absolute paths for file operations:
- Relative paths (recommended): "notes/meeting.md" - automatically resolved from the project directory
- Absolute paths: "{project_working_dir}/notes/meeting.md" - also supported

"""

    if tool_schemas:
        base_prompt += """
# TOOL CALLING

To use tools, output ONLY this (no other text):
```json
{"tool_calls": [{"name": "tool_name", "arguments": {"param": "value"}}]}
```

RIGHT:
User: "read package.json"
You: ```json
{"tool_calls": [{"name": "read_file", "arguments": {"path": "package.json"}}]}
```

WRONG:
User: "read package.json"
You: "Let me read that file."
```json
{"tool_calls": [{"name": "read_file", "arguments": {"path": "package.json"}}]}
```
^ FAILS because of text before JSON

WRONG:
User: "read package.json"  
You: ```json
{"name": "read_file", "arguments": {"path": "package.json"}}
```
^ FAILS because missing "tool_calls" array wrapper

Rule: Need info? → Output pure JSON. Have info? → Answer normally.

"""
        base_prompt += "# AVAILABLE TOOLS:\n\n"
        
        for tool in tool_schemas:
            base_prompt += f"## {tool['name']}\n"
            base_prompt += f"Description: {tool['description']}\n"
            base_prompt += f"Parameters:\n```json\n{json.dumps(tool['parameters'], indent=2)}\n```\n\n"
    
    return base_prompt


async def track_with_maintenance_agent(
    project_id: str,
    role: str,
    content: str
):
    """Send message to maintenance agent for context tracking"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8002/maintenance/context/message",
                json={
                    "project_id": project_id,
                    "role": role,
                    "content": content
                },
                timeout=2.0  # Don't wait long
            )
    except Exception:
        pass  # Don't fail if maintenance agent down


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
