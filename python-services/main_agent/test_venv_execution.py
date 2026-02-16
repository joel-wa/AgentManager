"""
Test script for venv execution functionality
Demonstrates how commands are executed in project-specific venvs
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from tool_logic import ToolExecutor, VenvManager


async def test_venv_creation():
    """Test 1: Venv creation"""
    print("\n=== Test 1: Venv Creation ===")
    
    project_id = "test-project-123"
    venv_manager = VenvManager()
    
    # Check if venv exists
    exists = venv_manager.venv_exists(project_id)
    print(f"Venv exists for {project_id}: {exists}")
    
    # Create venv
    success, message = await venv_manager.create_venv(project_id)
    print(f"Create venv result: {success}")
    print(f"Message: {message}")
    
    # Check again
    exists = venv_manager.venv_exists(project_id)
    print(f"Venv exists after creation: {exists}")
    
    # Get executables
    python_exe = venv_manager.get_python_executable(project_id)
    pip_exe = venv_manager.get_pip_executable(project_id)
    print(f"Python executable: {python_exe}")
    print(f"Pip executable: {pip_exe}")
    
    return venv_manager, project_id


async def test_command_execution(project_id: str):
    """Test 2: Execute commands with venv"""
    print("\n=== Test 2: Command Execution with Venv ===")
    
    # Create tool executor with project_id
    executor = ToolExecutor(
        working_directory=os.getcwd(),
        project_id=project_id
    )
    
    # Test various Python/pip command patterns
    test_commands = [
        # Standard commands
        ("python --version", "Standard python command"),
        ("pip list", "Standard pip command"),
        
        # Version-specific commands
        ("python3 --version", "python3 variant"),
        ("pip3 list", "pip3 variant"),
        
        # Python launcher (Windows)
        ("py --version", "Windows py launcher"),
        ("py -3.11 --version", "py with version specifier"),
        
        # Module invocation
        ("python -m pip list", "python -m pip pattern"),
        ("py -m pip list", "py -m pip pattern"),
        
        # Installation test (only one to avoid spam)
        ("pip install requests", "Package installation"),
    ]
    
    for cmd, description in test_commands:
        print(f"\n--- Test: {description} ---")
        print(f"Command: {cmd}")
        
        result = await executor.execute("execute_command", {
            "command": cmd
        })
        
        print(f"Success: {result.success}")
        if result.success and result.result:
            stdout = result.result.get('stdout', '')
            if stdout:
                # Show first 150 chars of output
                print(f"Output: {stdout[:150]}{'...' if len(stdout) > 150 else ''}")
        if result.error:
            print(f"Error: {result.error}")
        
        # Small delay between commands
        await asyncio.sleep(0.5)
    
    # Verify installation worked
    print("\n--- Verification: Check installed package ---")
    result = await executor.execute("execute_command", {
        "command": "pip show requests"
    })
    print(f"Success: {result.success}")
    if result.success:
        print(f"requests package info:\n{result.result.get('stdout', '')[:200]}...")
    
    # Test regular command (should NOT be transformed)
    print("\n--- Test: Regular command (should not use venv) ---")
    if sys.platform == "win32":
        cmd = "echo Hello from PowerShell"
    else:
        cmd = "echo Hello from bash"
    
    result = await executor.execute("execute_command", {
        "command": cmd
    })
    print(f"Success: {result.success}")
    print(f"Output: {result.result.get('stdout', '')}")


async def test_cleanup(venv_manager: VenvManager, project_id: str):
    """Test 3: Cleanup"""
    print("\n=== Test 3: Cleanup ===")
    
    # Optionally delete venv
    print(f"\nVenv location: {venv_manager.get_venv_path(project_id)}")
    print("To delete this venv, uncomment the cleanup code in the test script")
    
    # Uncomment to actually delete:
    # success, message = venv_manager.delete_venv(project_id)
    # print(f"Delete result: {success}")
    # print(f"Message: {message}")


async def main():
    """Run all tests"""
    print("=".format * 50)
    print("Testing Venv Execution System")
    print("=" * 50)
    
    try:
        # Test 1: Create venv
        venv_manager, project_id = await test_venv_creation()
        
        # Test 2: Execute commands
        await test_command_execution(project_id)
        
        # Test 3: Cleanup info
        await test_cleanup(venv_manager, project_id)
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nError during tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
