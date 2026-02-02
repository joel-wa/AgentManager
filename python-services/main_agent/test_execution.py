"""
Test script to verify tool calls are ACTUALLY executed, not just detected
"""

import asyncio
import httpx
import json
import os
import tempfile


async def test_real_tool_execution():
    """Test that tools actually execute and return real results"""
    print("=" * 60)
    print("TEST: Real Tool Execution (Not Smoke and Mirrors!)")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create a temporary test file for reading
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_file_path = f.name
            test_content = "This is test content for tool execution verification!"
            f.write(test_content)
        
        try:
            print(f"\n1. Testing read_file tool")
            print(f"   Reading: {test_file_path}")
            
            # Test read_file tool directly
            read_response = await client.post(
                "http://localhost:8001/agent/execute-tool",
                params={"tool_name": "read_file"},
                json={"path": test_file_path}
            )
            
            if read_response.status_code == 200:
                read_data = read_response.json()
                if read_data["success"]:
                    content = read_data["result"]["content"]
                    print(f"   ✓ Tool executed successfully!")
                    print(f"   ✓ Content read: '{content[:50]}...'")
                    print(f"   ✓ File size: {read_data['result']['size_bytes']} bytes")
                    
                    if content == test_content:
                        print(f"   ✓ Content matches! Tool ACTUALLY READ the file!")
                    else:
                        print(f"   ✗ Content mismatch - something is wrong")
                        return False
                else:
                    print(f"   ✗ Tool failed: {read_data.get('error')}")
                    return False
            else:
                print(f"   ✗ HTTP Error: {read_response.status_code}")
                return False
            
            # Test write_file tool
            write_test_path = os.path.join(tempfile.gettempdir(), "agent_test_write.txt")
            write_test_content = "Agent wrote this file!"
            
            print(f"\n2. Testing write_file tool")
            print(f"   Writing to: {write_test_path}")
            
            write_response = await client.post(
                "http://localhost:8001/agent/execute-tool",
                params={"tool_name": "write_file"},
                json={"path": write_test_path, "content": write_test_content}
            )
            
            if write_response.status_code == 200:
                write_data = write_response.json()
                if write_data["success"]:
                    print(f"   ✓ Tool executed successfully!")
                    print(f"   ✓ Bytes written: {write_data['result']['bytes_written']}")
                    
                    # Verify the file was actually created
                    if os.path.exists(write_test_path):
                        with open(write_test_path, 'r') as f:
                            actual_content = f.read()
                        if actual_content == write_test_content:
                            print(f"   ✓ File actually created with correct content!")
                        else:
                            print(f"   ✗ File content mismatch")
                            return False
                        os.remove(write_test_path)  # Clean up
                    else:
                        print(f"   ✗ File was not actually created!")
                        return False
                else:
                    print(f"   ✗ Tool failed: {write_data.get('error')}")
                    return False
            else:
                print(f"   ✗ HTTP Error: {write_response.status_code}")
                return False
            
            # Test list_directory tool
            test_dir = tempfile.gettempdir()
            print(f"\n3. Testing list_directory tool")
            print(f"   Listing: {test_dir}")
            
            list_response = await client.post(
                "http://localhost:8001/agent/execute-tool",
                params={"tool_name": "list_directory"},
                json={"path": test_dir, "recursive": False}
            )
            
            if list_response.status_code == 200:
                list_data = list_response.json()
                if list_data["success"]:
                    entries = list_data["result"]["entries"]
                    print(f"   ✓ Tool executed successfully!")
                    print(f"   ✓ Found {len(entries)} entries")
                    print(f"   ✓ Sample entries:")
                    for entry in entries[:5]:
                        print(f"      - {entry['name']} ({entry['type']})")
                    
                    if len(entries) > 0:
                        print(f"   ✓ Directory actually listed!")
                    else:
                        print(f"   ⚠ No entries found (might be empty directory)")
                else:
                    print(f"   ✗ Tool failed: {list_data.get('error')}")
                    return False
            else:
                print(f"   ✗ HTTP Error: {list_response.status_code}")
                return False
            
            # Test via chat endpoint (integration test)
            print(f"\n4. Testing tool execution via chat endpoint")
            print(f"   Asking agent to read the test file...")
            
            chat_response = await client.post(
                "http://localhost:8001/agent/chat",
                json={
                    "message": f"Read the file at {test_file_path}",
                    "tools": ["read_file"]
                }
            )
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                
                if chat_data.get("tool_calls"):
                    print(f"   ✓ Agent generated tool calls")
                    for tc in chat_data["tool_calls"]:
                        print(f"      - {tc['name']}({tc['arguments']})")
                else:
                    print(f"   ⚠ Agent did not generate tool calls")
                
                if chat_data.get("tool_results"):
                    print(f"   ✓ Tools were ACTUALLY EXECUTED!")
                    for tr in chat_data["tool_results"]:
                        if tr["success"]:
                            print(f"      ✓ {tr['tool_name']}: SUCCESS")
                            if tr["tool_name"] == "read_file" and tr["result"]:
                                file_content = tr["result"].get("content", "")
                                if test_content in file_content:
                                    print(f"      ✓ Correct file content returned!")
                                else:
                                    print(f"      ✗ Wrong content returned")
                                    return False
                        else:
                            print(f"      ✗ {tr['tool_name']}: FAILED - {tr['error']}")
                            return False
                else:
                    print(f"   ✗ NO TOOL RESULTS - Tools were NOT executed!")
                    print(f"   This means it's SMOKE AND MIRRORS!")
                    return False
            else:
                print(f"   ✗ HTTP Error: {chat_response.status_code}")
                return False
            
            print(f"\n" + "=" * 60)
            print(f"✓ ALL TESTS PASSED!")
            print(f"Tools are ACTUALLY being executed, not just detected!")
            print(f"=" * 60)
            return True
            
        finally:
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)


async def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Tool Execution Verification Test" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\nVerifying that tools are ACTUALLY executed, not just detected...\n")
    
    success = await test_real_tool_execution()
    
    if success:
        print("\n🎉 SUCCESS! Tools are working for real!")
    else:
        print("\n❌ FAILURE! Tools are NOT actually executing!")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
