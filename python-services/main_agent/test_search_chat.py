"""
Test search through the chat interface
"""

import asyncio
import httpx

async def test_chat_with_search():
    """Test the agent with a search query"""
    
    url = "http://localhost:8001/agent/chat"
    
    request = {
        "message": "Search for files containing 'FastAPI' in the workspace",
        "tools": ["search", "read_file"],
        "workspace_root": ".",
        "chat_history": []
    }
    
    print("Sending chat request with search query...")
    print(f"Message: {request['message']}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=request)
            
            if response.status_code == 200:
                data = response.json()
                print("✓ Response received!")
                print(f"\nAgent Response:\n{data.get('response', 'No response')}")
                
                if 'tool_calls' in data and data['tool_calls']:
                    print(f"\n✓ Tool calls made: {len(data['tool_calls'])}")
                    for tool_call in data['tool_calls']:
                        print(f"  - {tool_call.get('name')}: {tool_call.get('arguments', {})}")
                else:
                    print("\n⚠ No tool calls made")
            else:
                print(f"✗ Error: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        print("\nMake sure the main agent is running: python main.py")

if __name__ == "__main__":
    asyncio.run(test_chat_with_search())
