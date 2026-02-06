"""
Test the search tool functionality
"""

import asyncio
from tool_logic import SearchTool

async def test_search():
    search_tool = SearchTool()
    
    # Test 1: Search for "agent"
    print("Test 1: Searching for 'agent'...")
    result = await search_tool.execute({
        "query": "agent",
        "max_results": 5,
        "_working_directory": "."
    })
    
    if result.success:
        print(f"✓ Search succeeded!")
        print(f"  Found {result.result['total_found']} matches")
        for match in result.result['matches'][:3]:
            print(f"  - {match['file']}:{match['line']} - {match['content'][:80]}...")
    else:
        print(f"✗ Search failed: {result.error}")
    
    print()
    
    # Test 2: Search for "FastAPI"
    print("Test 2: Searching for 'FastAPI'...")
    result = await search_tool.execute({
        "query": "FastAPI",
        "max_results": 3,
        "_working_directory": "."
    })
    
    if result.success:
        print(f"✓ Search succeeded!")
        print(f"  Found {result.result['total_found']} matches")
        for match in result.result['matches']:
            print(f"  - {match['file']}:{match['line']}")
    else:
        print(f"✗ Search failed: {result.error}")
    
    print()
    
    # Test 3: Search for something that doesn't exist
    print("Test 3: Searching for 'xyzabc123notfound'...")
    result = await search_tool.execute({
        "query": "xyzabc123notfound",
        "max_results": 5,
        "_working_directory": "."
    })
    
    if result.success:
        print(f"✓ Search succeeded!")
        print(f"  Found {result.result['total_found']} matches (should be 0)")
    else:
        print(f"✗ Search failed: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_search())
