"""
Test script to verify agent can see and use tools properly
"""

import asyncio
import httpx
import json


async def test_tools_endpoint():
    """Test that we can list available tools"""
    print("=" * 60)
    print("TEST 1: List Available Tools")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8001/agent/tools")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Found {data['count']} tools")
                print("\nTools:")
                for tool in data['tools']:
                    print(f"\n  - {tool['name']}")
                    print(f"    Description: {tool['description']}")
                    print(f"    Parameters: {json.dumps(tool['parameters'], indent=6)}")
                return True
            else:
                print(f"✗ Failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False


async def test_tool_in_system_prompt():
    """Test that tools are properly formatted in system prompt"""
    print("\n" + "=" * 60)
    print("TEST 2: Check System Prompt with Tools")
    print("=" * 60)
    
    from tool_logic import ToolExecutor
    from main import build_system_prompt
    
    executor = ToolExecutor()
    tool_schemas = executor.get_tool_schemas()
    
    # Get first 3 tools for testing
    test_tools = tool_schemas[:3]
    
    system_prompt = build_system_prompt(test_tools)
    
    print("\nGenerated System Prompt:")
    print("-" * 60)
    print(system_prompt[:1000])  # First 1000 chars
    print("..." if len(system_prompt) > 1000 else "")
    print("-" * 60)
    
    # Check for key elements
    checks = [
        ("JSON format instructions", "```json" in system_prompt),
        ("Tool names present", all(t['name'] in system_prompt for t in test_tools)),
        ("Parameters schema", "Parameters:" in system_prompt),
        ("Usage instructions", "tool_calls" in system_prompt)
    ]
    
    print("\nSystem Prompt Checks:")
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
    
    return all(passed for _, passed in checks)


async def test_chat_with_tools():
    """Test sending a chat message with tools enabled"""
    print("\n" + "=" * 60)
    print("TEST 3: Chat with Tools Enabled")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # First check if Ollama is available
            health = await client.get("http://localhost:8001/health")
            if health.status_code != 200:
                print("✗ Service not healthy")
                return False
            
            health_data = health.json()
            if not health_data.get("model_available"):
                print("✗ Model not available - skipping chat test")
                print(f"  Ollama URL: {health_data.get('ollama_url')}")
                return None  # Skip, not a failure
            
            # Send a test message that should trigger tool use
            test_message = "Can you search for files containing 'agent' in the workspace?"
            
            print(f"\nSending message: '{test_message}'")
            print(f"Tools enabled: ['search', 'read_file']")
            
            response = await client.post(
                "http://localhost:8001/agent/chat",
                json={
                    "message": test_message,
                    "tools": ["search", "read_file"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ Got response")
                print(f"\nAgent Response:")
                print("-" * 60)
                print(data['response'][:500])
                print("..." if len(data['response']) > 500 else "")
                print("-" * 60)
                
                if data.get('tool_calls'):
                    print(f"\n✓ Agent generated {len(data['tool_calls'])} tool call(s):")
                    for i, tc in enumerate(data['tool_calls'], 1):
                        print(f"\n  Tool Call {i}:")
                        print(f"    Name: {tc['name']}")
                        print(f"    Arguments: {json.dumps(tc['arguments'], indent=6)}")
                    return True
                else:
                    print("\n⚠ Agent did not generate any tool calls")
                    print("  This might be expected if the model doesn't understand the format")
                    return False
            else:
                print(f"✗ Request failed: {response.status_code}")
                print(f"  {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            return False


async def test_tool_call_parsing():
    """Test that tool call parsing works correctly"""
    print("\n" + "=" * 60)
    print("TEST 4: Tool Call Parsing")
    print("=" * 60)
    
    from ollama_client import OllamaClient
    
    client = OllamaClient()
    
    # Test cases with different formats
    test_cases = [
        {
            "name": "JSON format",
            "content": """Sure! I'll search for that.

```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {"query": "agent", "max_results": 10}
    }
  ]
}
```

I've initiated the search.""",
            "available_tools": ["search", "read_file"],
            "expected_calls": 1
        },
        {
            "name": "Legacy format",
            "content": 'I will search for that. [TOOL: search("agent")]',
            "available_tools": ["search"],
            "expected_calls": 1
        },
        {
            "name": "No tool calls",
            "content": "I cannot help with that right now.",
            "available_tools": ["search"],
            "expected_calls": 0
        }
    ]
    
    all_passed = True
    for test_case in test_cases:
        name = test_case["name"]
        content = test_case["content"]
        available = test_case["available_tools"]
        expected = test_case["expected_calls"]
        
        result = client._parse_tool_calls(content, available)
        actual = len(result) if result else 0
        
        passed = actual == expected
        status = "✓" if passed else "✗"
        print(f"  {status} {name}: Expected {expected} calls, got {actual}")
        
        if result and passed:
            for call in result:
                print(f"      - {call['name']}({call['arguments']})")
        
        all_passed = all_passed and passed
    
    return all_passed


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Agent Tool System Test Suite" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\nTesting if the agent can see and use its tools properly...\n")
    
    results = []
    
    # Test 1: Tools endpoint
    result1 = await test_tools_endpoint()
    results.append(("List Tools Endpoint", result1))
    
    # Test 2: System prompt generation
    result2 = await test_tool_in_system_prompt()
    results.append(("System Prompt Generation", result2))
    
    # Test 3: Tool call parsing
    result3 = await test_tool_call_parsing()
    results.append(("Tool Call Parsing", result3))
    
    # Test 4: Live chat (may be skipped if Ollama not available)
    result4 = await test_chat_with_tools()
    if result4 is not None:
        results.append(("Live Chat with Tools", result4))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:>8} - {test_name}")
    
    print("\n" + "-" * 60)
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! The agent can see and use its tools.")
    else:
        print(f"\n⚠ {total_count - passed_count} test(s) failed. Please review the output above.")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
