"""
Test that workspace_root is correctly passed to the search tool
"""

import asyncio
import httpx
import os

async def test_workspace_root():
    """Test that search uses the correct workspace directory"""
    
    url = "http://localhost:8001/agent/chat"
    
    # Get the real workspace root (parent of python-services)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    
    print(f"Current directory: {current_dir}")
    print(f"Workspace root: {workspace_root}")
    print()
    
    # Test 1: Without workspace_root (should search current directory)
    print("Test 1: Search WITHOUT workspace_root")
    request1 = {
        "message": "Search for 'rust-core' in the workspace",
        "tools": ["search"],
        # NO workspace_root passed
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=request1)
            if response.status_code == 200:
                data = response.json()
                print(f"Response preview: {data.get('response', '')[:200]}...")
                if 'tool_calls' in data and data['tool_calls']:
                    for tc in data['tool_calls']:
                        if tc['name'] == 'search':
                            print(f"  Search performed (working_dir not visible in args)")
            print()
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Test 2: With workspace_root (should search the workspace)
    print("Test 2: Search WITH workspace_root")
    request2 = {
        "message": "Search for 'rust-core' in the workspace",
        "tools": ["search"],
        "workspace_root": workspace_root,  # Pass workspace root
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=request2)
            if response.status_code == 200:
                data = response.json()
                print(f"Response preview: {data.get('response', '')[:200]}...")
                
                # Check if it found files in different directories
                response_text = data.get('response', '')
                if 'rust-core' in response_text.lower():
                    print("✓ Found 'rust-core' references!")
                    if 'Cargo.toml' in response_text or 'coordinator.rs' in response_text:
                        print("✓ Found Rust files - workspace root was used!")
                    else:
                        print("⚠ Only found python files - might not be searching whole workspace")
                else:
                    print("✗ Didn't find 'rust-core' - search might not be working")
            print()
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Test 3: Search for something in frontend directory
    print("Test 3: Search for 'React' with workspace_root")
    request3 = {
        "message": "Search for 'React' in the workspace",
        "tools": ["search"],
        "workspace_root": workspace_root,
        "max_results": 3
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=request3)
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                if 'frontend' in response_text.lower() or 'tsx' in response_text.lower():
                    print("✓ Found React in frontend files - full workspace search working!")
                else:
                    print("⚠ Didn't find frontend React files")
                    
                print(f"Response preview: {response_text[:250]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_workspace_root())
