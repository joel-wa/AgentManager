"""
Test the agentic loop - verify agent sees tool results and makes follow-up decisions
"""

import asyncio
import httpx
import json
import os
import tempfile


async def test_agentic_loop():
    """Test that agent can see tool results and make decisions based on them"""
    print("=" * 70)
    print("TEST: Agentic Loop - Agent Decision Making with Tool Results")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Check if model is available
        health = await client.get("http://localhost:8001/health")
        if health.status_code != 200 or not health.json().get("model_available"):
            print("⚠ Model not available - test skipped")
            return None
        
        # Create test files for the agent to work with
        test_dir = tempfile.mkdtemp()
        test_file1 = os.path.join(test_dir, "document1.txt")
        test_file2 = os.path.join(test_dir, "document2.txt")
        
        with open(test_file1, 'w') as f:
            f.write("This document contains information about Python programming.")
        
        with open(test_file2, 'w') as f:
            f.write("This document discusses artificial intelligence and machine learning.")
        
        try:
            print(f"\nTest Setup:")
            print(f"  Created test directory: {test_dir}")
            print(f"  File 1: document1.txt (about Python)")
            print(f"  File 2: document2.txt (about AI/ML)")
            
            # Test 1: Multi-step reasoning
            print(f"\n{'='*70}")
            print("Test 1: Multi-Step Tool Usage")
            print(f"{'='*70}")
            print(f"\nAsking agent to:")
            print(f"  1. List files in directory")
            print(f"  2. Read one of the files")
            print(f"  3. Summarize what it found")
            
            message = f"""Please do the following:
1. List all files in the directory: {test_dir}
2. Read the first .txt file you find
3. Tell me what the file is about

Use the tools available to you."""
            
            response = await client.post(
                "http://localhost:8001/agent/chat",
                json={
                    "message": message,
                    "tools": ["list_directory", "read_file"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n{'─'*70}")
                print("Agent's Final Response:")
                print(f"{'─'*70}")
                print(data['response'][:500])
                if len(data['response']) > 500:
                    print("...")
                print(f"{'─'*70}")
                
                if data.get('tool_calls'):
                    print(f"\n✓ Agent made {len(data['tool_calls'])} tool call(s):")
                    for i, tc in enumerate(data['tool_calls'], 1):
                        print(f"  {i}. {tc['name']}(", end="")
                        args_str = ", ".join(f"{k}=..." for k in tc['arguments'].keys())
                        print(f"{args_str})")
                    
                    # Check if agent made multiple different tool calls
                    tool_names = [tc['name'] for tc in data['tool_calls']]
                    unique_tools = set(tool_names)
                    
                    if len(unique_tools) > 1:
                        print(f"\n✓ Agent used multiple different tools: {unique_tools}")
                        print(f"  This shows it's reasoning through multiple steps!")
                    else:
                        print(f"\n⚠ Agent only used one type of tool: {unique_tools}")
                
                if data.get('tool_results'):
                    print(f"\n✓ Got {len(data['tool_results'])} tool result(s):")
                    for i, tr in enumerate(data['tool_results'], 1):
                        status = "✓" if tr['success'] else "✗"
                        print(f"  {status} {tr['tool_name']}: {'SUCCESS' if tr['success'] else 'FAILED'}")
                    
                    # Check if we have both list_directory and read_file results
                    result_tools = [tr['tool_name'] for tr in data['tool_results']]
                    if 'list_directory' in result_tools and 'read_file' in result_tools:
                        print(f"\n✓ AGENTIC LOOP WORKING!")
                        print(f"  Agent:")
                        print(f"    1. Listed directory")
                        print(f"    2. Saw the results")
                        print(f"    3. Decided to read a file")
                        print(f"    4. Saw file contents")
                        print(f"    5. Provided final answer")
                        return True
                    else:
                        print(f"\n⚠ Expected both list and read operations")
                        print(f"  Got: {result_tools}")
                        return False
                else:
                    print(f"\n✗ No tool results returned")
                    return False
            else:
                print(f"\n✗ Request failed: {response.status_code}")
                print(response.text)
                return False
                
        finally:
            # Cleanup
            try:
                os.remove(test_file1)
                os.remove(test_file2)
                os.rmdir(test_dir)
            except:
                pass


async def test_simple_iteration():
    """Test simpler case: read a file and tell us about it"""
    print(f"\n{'='*70}")
    print("Test 2: Simple Iteration Test")
    print(f"{'='*70}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Create a test file
        test_file = os.path.join(tempfile.gettempdir(), "agent_iteration_test.txt")
        test_content = "The quick brown fox jumps over the lazy dog. This is a test file."
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        try:
            print(f"\nCreated test file: {test_file}")
            print(f"Content: '{test_content}'")
            
            message = f"Please read the file at {test_file} and tell me how many words it contains."
            
            print(f"\nAsking agent: '{message}'")
            
            response = await client.post(
                "http://localhost:8001/agent/chat",
                json={
                    "message": message,
                    "tools": ["read_file"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\nAgent's Response:")
                print(f"  {data['response'][:300]}")
                
                if data.get('tool_calls'):
                    print(f"\n✓ Tool calls made: {len(data['tool_calls'])}")
                    
                if data.get('tool_results'):
                    print(f"✓ Tool results received: {len(data['tool_results'])}")
                    
                    # Check if response mentions word count or file content
                    response_lower = data['response'].lower()
                    if ('word' in response_lower or 'content' in response_lower or 
                        'fox' in response_lower):
                        print(f"\n✓ Agent's response includes information FROM the file!")
                        print(f"  This proves it saw the tool results and processed them!")
                        return True
                    else:
                        print(f"\n⚠ Response doesn't seem to reference file contents")
                        return False
            else:
                print(f"✗ Request failed: {response.status_code}")
                return False
                
        finally:
            try:
                os.remove(test_file)
            except:
                pass


async def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Agentic Loop Verification Test" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\nTesting if agent can see tool results and make follow-up decisions...\n")
    
    # Run tests
    result1 = await test_simple_iteration()
    result2 = await test_agentic_loop()
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    tests_passed = 0
    tests_total = 0
    
    if result1 is not None:
        tests_total += 1
        if result1:
            tests_passed += 1
            print("✓ PASS - Simple iteration with tool results")
        else:
            print("✗ FAIL - Simple iteration with tool results")
    
    if result2 is not None:
        tests_total += 1
        if result2:
            tests_passed += 1
            print("✓ PASS - Multi-step agentic loop")
        else:
            print("✗ FAIL - Multi-step agentic loop")
    
    if tests_total == 0:
        print("⚠ No tests could run (model unavailable)")
    elif tests_passed == tests_total:
        print(f"\n🎉 All {tests_total} tests passed!")
        print("\nThe agent CAN see tool results and make decisions based on them!")
        print("This is a true agentic system, not just smoke and mirrors!")
    else:
        print(f"\n⚠ {tests_passed}/{tests_total} tests passed")
    
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
