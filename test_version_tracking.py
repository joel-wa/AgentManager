#!/usr/bin/env python3
"""
Test script for file version tracking feature.
This script tests the version tracking API endpoints.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_create_project():
    """Create a test project"""
    print_section("Creating Test Project")
    
    response = requests.post(f"{BASE_URL}/projects", json={
        "name": "Version Tracking Test",
        "description": "Testing file version tracking feature"
    })
    
    if response.status_code == 200:
        project = response.json()
        project_id = project["id"]
        print(f"✓ Project created successfully")
        print(f"  Project ID: {project_id}")
        return project_id
    else:
        print(f"✗ Failed to create project: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_write_file(project_id, path, content):
    """Write a file to the project"""
    print(f"\nWriting file: {path}")
    
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/files/{path}",
        data=content,
        headers={"Content-Type": "text/plain"}
    )
    
    if response.status_code == 200:
        print(f"✓ File written successfully")
        return True
    else:
        print(f"✗ Failed to write file: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def test_list_versions(project_id, path):
    """List all versions of a file"""
    print(f"\nListing versions for: {path}")
    
    response = requests.get(f"{BASE_URL}/projects/{project_id}/files/{path}/versions")
    
    if response.status_code == 200:
        history = response.json()
        print(f"✓ Version history retrieved")
        print(f"  Current version: {history['current_version']}")
        print(f"  Total versions: {len(history['versions'])}")
        
        if history['versions']:
            print("\n  Version details:")
            for v in history['versions']:
                timestamp = datetime.fromisoformat(v['timestamp'].replace('Z', '+00:00'))
                print(f"    - v{v['version']}: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"      Size: {v['file_size']} bytes, Hash: {v['content_hash'][:16]}...")
                if v.get('message'):
                    print(f"      Message: {v['message']}")
        
        return history
    else:
        print(f"✗ Failed to list versions: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_get_version(project_id, path, version):
    """Get a specific version of a file"""
    print(f"\nGetting version {version} of: {path}")
    
    response = requests.get(f"{BASE_URL}/projects/{project_id}/files/{path}/versions/{version}")
    
    if response.status_code == 200:
        version_entry = response.json()
        print(f"✓ Version {version} retrieved")
        print(f"  Content preview: {version_entry['content'][:100]}...")
        return version_entry
    else:
        print(f"✗ Failed to get version: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_restore_version(project_id, path, version):
    """Restore a file to a specific version"""
    print(f"\nRestoring {path} to version {version}")
    
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/files/{path}/versions/{version}/restore"
    )
    
    if response.status_code == 200:
        print(f"✓ File restored to version {version}")
        return True
    else:
        print(f"✗ Failed to restore version: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def test_read_file(project_id, path):
    """Read current file content"""
    print(f"\nReading current file: {path}")
    
    response = requests.get(f"{BASE_URL}/projects/{project_id}/files/{path}")
    
    if response.status_code == 200:
        content = response.text
        print(f"✓ File read successfully")
        print(f"  Content preview: {content[:100]}...")
        return content
    else:
        print(f"✗ Failed to read file: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def main():
    """Run all tests"""
    print("=" * 60)
    print("  File Version Tracking Test Suite")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("✗ Server is not responding properly")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Is it running on port 8000?")
        return
    
    print("✓ Server is running")
    
    # Create test project
    project_id = test_create_project()
    if not project_id:
        return
    
    # Test file path
    test_file = "test_versioning.txt"
    
    # Test 1: Write initial version
    print_section("Test 1: Write Initial Version")
    test_write_file(project_id, test_file, "This is version 1 of the file.\n")
    time.sleep(0.5)
    
    # Test 2: Write second version
    print_section("Test 2: Write Second Version")
    test_write_file(project_id, test_file, "This is version 1 of the file.\nThis is version 2 - added a line.\n")
    time.sleep(0.5)
    
    # Test 3: Write third version
    print_section("Test 3: Write Third Version")
    test_write_file(project_id, test_file, "This is version 1 of the file.\nThis is version 2 - added a line.\nThis is version 3 - added another line.\n")
    time.sleep(0.5)
    
    # Test 4: List all versions
    print_section("Test 4: List All Versions")
    history = test_list_versions(project_id, test_file)
    
    if not history or not history['versions']:
        print("\n✗ No versions found. Version tracking may not be working.")
        return
    
    # Test 5: Get specific version
    print_section("Test 5: Get Specific Version")
    if len(history['versions']) >= 2:
        test_get_version(project_id, test_file, 2)
    
    # Test 6: Read current file
    print_section("Test 6: Read Current File")
    current_content = test_read_file(project_id, test_file)
    
    # Test 7: Restore to version 1
    print_section("Test 7: Restore to Version 1")
    if len(history['versions']) >= 1:
        test_restore_version(project_id, test_file, 1)
        time.sleep(0.5)
        
        # Verify restoration
        restored_content = test_read_file(project_id, test_file)
        if restored_content and "This is version 1 of the file.\n" == restored_content:
            print("✓ File content matches version 1")
        else:
            print("✗ File content does not match version 1")
    
    # Test 8: Check version history after restoration
    print_section("Test 8: Version History After Restoration")
    final_history = test_list_versions(project_id, test_file)
    
    if final_history and len(final_history['versions']) > len(history['versions']):
        print("✓ New version created during restoration (as expected)")
    
    print_section("Test Complete")
    print(f"\nProject ID: {project_id}")
    print("You can manually verify the version tracking in the file system at:")
    print(f"  ~/.agent-workspace/projects/{project_id}/.meta/versions/")

if __name__ == "__main__":
    main()
