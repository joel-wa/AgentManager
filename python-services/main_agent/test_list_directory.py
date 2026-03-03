"""
Test script for list_directory with smart filtering
Demonstrates how recursive listing now prevents context overflow
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from tool_logic import ToolExecutor


async def test_non_recursive():
    """Test 1: Non-recursive listing (current directory only)"""
    print("\n=== Test 1: Non-recursive Listing ===")
    
    executor = ToolExecutor(working_directory=os.getcwd())
    
    result = await executor.execute("list_directory", {
        "path": ".",
        "recursive": False
    })
    
    print(f"Success: {result.success}")
    if result.success:
        data = result.result
        print(f"Path: {data['path']}")
        print(f"Count: {data['count']}")
        print(f"Entries (first 10):")
        for entry in data['entries'][:10]:
            print(f"  - {entry['name']} ({entry['type']})")
        if data['count'] > 10:
            print(f"  ... and {data['count'] - 10} more")


async def test_recursive_with_filtering():
    """Test 2: Recursive listing with automatic filtering"""
    print("\n=== Test 2: Recursive Listing (with smart filtering) ===")
    
    executor = ToolExecutor(working_directory=os.getcwd())
    
    result = await executor.execute("list_directory", {
        "path": ".",
        "recursive": True
    })
    
    print(f"Success: {result.success}")
    if result.success:
        data = result.result
        print(f"Path: {data['path']}")
        print(f"Count: {data['count']}")
        print(f"Truncated: {data.get('truncated', False)}")
        
        if 'excluded_dirs' in data:
            print(f"Excluded directories: {', '.join(data['excluded_dirs'])}")
        
        if 'note' in data:
            print(f"Note: {data['note']}")
        
        if 'warning' in data:
            print(f"⚠️ Warning: {data['warning']}")
        
        print(f"\nSample entries (first 15):")
        for entry in data['entries'][:15]:
            print(f"  - {entry['name']} ({entry['type']})")
        
        if data['count'] > 15:
            print(f"  ... and {data['count'] - 15} more")


async def test_recursive_large_limit():
    """Test 3: Recursive with custom entry limit"""
    print("\n=== Test 3: Recursive with Custom Limit (100 entries) ===")
    
    executor = ToolExecutor(working_directory=os.getcwd())
    
    result = await executor.execute("list_directory", {
        "path": ".",
        "recursive": True,
        "max_entries": 100
    })
    
    print(f"Success: {result.success}")
    if result.success:
        data = result.result
        print(f"Count: {data['count']}")
        print(f"Truncated: {data.get('truncated', False)}")
        
        if data.get('truncated'):
            print(f"✅ Successfully truncated at 100 entries (prevents overflow)")


async def test_specific_directory():
    """Test 4: List specific subdirectory"""
    print("\n=== Test 4: List Specific Subdirectory ===")
    
    # Try to list a known subdirectory
    test_dirs = ["../../rust-core", "../../frontend", "."]
    
    executor = ToolExecutor(working_directory=os.getcwd())
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            print(f"\nListing: {test_dir}")
            result = await executor.execute("list_directory", {
                "path": test_dir,
                "recursive": False
            })
            
            if result.success:
                data = result.result
                print(f"  Items: {data['count']}")
                dirs = [e['name'] for e in data['entries'] if e['type'] == 'directory']
                files = [e['name'] for e in data['entries'] if e['type'] == 'file']
                print(f"  Directories: {len(dirs)}")
                print(f"  Files: {len(files)}")
            break


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing list_directory Smart Filtering")
    print("=" * 60)
    
    try:
        await test_non_recursive()
        await test_recursive_with_filtering()
        await test_recursive_large_limit()
        await test_specific_directory()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        print("\n💡 Key Improvements:")
        print("  - Recursive listings exclude bloat directories")
        print("  - Maximum entry limit prevents context overflow")
        print("  - Clear warnings when truncated")
        print("  - Agent can now safely use recursive listings")
        
    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
