import requests
import time

print("=== Testing File Change with Enhanced Context ===\n")

# Test 1: Create a new utility file
data = {
    'project_id': '8e6f3a02-b81c-4cd7-abba-e193b0ad1245',
    'file_path': 'utils.py',
    'change_type': 'created',
    'workspace_path': r'C:\Users\RanVic\.agent-workspace\projects\8e6f3a02-b81c-4cd7-abba-e193b0ad1245',
    'file_content': '''def format_date(date_str):
    """Format date string"""
    return date_str

def validate_email(email):
    """Validate email format"""
    return "@" in email''',
    'readme_content': '# Test Project\n\nThis is a test project.',
    'workspace_structure': {
        'files': ['README.md', 'test_feature.py', 'data.json'],
        'folders': ['docs', 'src']
    }
}

print("Sending file change notification...")
response = requests.post('http://localhost:8002/maintenance/file-change', json=data)
print(f"Response: {response.text}\n")

print("Waiting 3 seconds for AI processing...")
time.sleep(3)

print("Checking for generated suggestions...")
response = requests.get('http://localhost:8002/maintenance/suggestions/8e6f3a02-b81c-4cd7-abba-e193b0ad1245')
suggestions = response.json().get('suggestions', [])

if suggestions:
    print(f"\n[OK] Generated {len(suggestions)} suggestion(s):\n")
    for i, s in enumerate(suggestions, 1):
        print(f"{i}. {s['title']}")
        print(f"   Type: {s['type']}")
        print(f"   Priority: {s['priority']}")
        print(f"   Description: {s['description']}")
        print(f"   Affected files: {', '.join(s['affected_files'])}\n")
else:
    print("[WARN] No suggestions generated yet\n")
