import requests
import time

print("=== Testing MAINTENANCE.md Integration ===\n")

# Update the MAINTENANCE.md to have specific rules
maintenance_content = """# Maintenance Configuration for Youtube Plan

## Project Context
You need to properly arrange documents and files in their respective folders.
All markdown files should be in the 'docs' folder.
All Python scripts should be in the 'scripts' folder.

## Important Files
- `README.md` - Project overview (keep in root)
- `soul.md` - Agent personality configuration (keep in root)
- `Recents.md` - Decision timeline (keep in root)

## Organization Rules
- **Rule 1**: Any new .md files (except README, soul, Recents) should be moved to 'docs' folder
- **Rule 2**: Python files should be in 'scripts' folder
- **Rule 3**: Always suggest updating README when major files are added

## Merge Rules
- Merge duplicate documentation files
- Keep most recent version

## Custom Health Checks
- [ ] README is up to date with latest changes
- [ ] All markdown docs are in 'docs' folder
"""

# Write updated MAINTENANCE.md
import os
project_path = r"C:\Users\RanVic\.agent-workspace\projects\8e6f3a02-b81c-4cd7-abba-e193b0ad1245"
os.makedirs(os.path.join(project_path, ".meta"), exist_ok=True)
with open(os.path.join(project_path, ".meta", "MAINTENANCE.md"), 'w', encoding='utf-8') as f:
    f.write(maintenance_content)
print("[OK] Updated MAINTENANCE.md with specific rules\n")

# Now create a new markdown file that should trigger the organization rule
data = {
    'project_id': '8e6f3a02-b81c-4cd7-abba-e193b0ad1245',
    'file_path': 'my_notes.md',  # Should trigger: move to docs folder
    'change_type': 'created',
    'workspace_path': project_path,
    'file_content': '# My Notes\n\nSome important notes about the project.',
    'readme_content': '# Youtube Plan',
    'workspace_structure': {
        'files': ['README.md', 'soul.md', 'Recents.md', 'my_notes.md'],
        'folders': ['docs', 'scripts']
    }
}

print("Sending file change notification for 'my_notes.md'...")
response = requests.post('http://localhost:8002/maintenance/file-change', json=data)
print(f"Response: {response.text}\n")

print("Waiting 4 seconds for AI processing...")
time.sleep(4)

print("Checking suggestions...")
response = requests.get('http://localhost:8002/maintenance/suggestions/8e6f3a02-b81c-4cd7-abba-e193b0ad1245')
suggestions = response.json().get('suggestions', [])

print(f"\n{'='*60}")
print(f"Generated {len(suggestions)} suggestions:")
print(f"{'='*60}\n")

for i, s in enumerate(suggestions, 1):
    print(f"{i}. [{s['type'].upper()}] {s['title']}")
    print(f"   Priority: {s['priority']}")
    print(f"   Description: {s['description']}")
    print(f"   Affected files: {', '.join(s.get('affected_files', []))}")
    
    # Check if it mentions moving to docs folder (from MAINTENANCE.md rules)
    if 'docs' in s['description'].lower() or 'docs' in s['title'].lower():
        print(f"   ✓ USES MAINTENANCE.md RULE!")
    print()

print("\nLooking for evidence of MAINTENANCE.md usage:")
print("- Should suggest moving my_notes.md to docs folder")
print("- Should mention updating README (as per rules)")
