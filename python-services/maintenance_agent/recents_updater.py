"""
Auto-update Recents.md timeline with significant changes
"""

import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from models import ContextSnapshot, ChangeImpact


class RecentsUpdater:
    """Automatically update Recents.md with significant changes"""
    
    def __init__(self, projects_root: str = None):
        if projects_root is None:
            # Try to get from environment, fall back to relative path
            projects_root = os.environ.get('WORKSPACE_PROJECTS_ROOT') or os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "projects")
        self.projects_root = projects_root
    
    async def update_recents(
        self,
        project_id: str,
        file_path: str,
        context: ContextSnapshot,
        impact: ChangeImpact
    ):
        """Auto-update Recents.md with new entry"""
        try:
            recents_path = os.path.join(self.projects_root, project_id, "Recents.md")
            
            # Ensure project directory exists
            os.makedirs(os.path.dirname(recents_path), exist_ok=True)
            
            # Read existing content
            existing_content = await self._read_file(recents_path)
            
            # Generate entry
            entry = self._generate_entry(file_path, context, impact)
            
            # Insert at top (after header)
            updated_content = self._insert_recent_entry(existing_content, entry)
            
            # Write back
            await self._write_file(recents_path, updated_content)
            
        except Exception as e:
            print(f"Error updating Recents.md: {e}")
    
    def _generate_entry(
        self,
        file_path: str,
        context: ContextSnapshot,
        impact: ChangeImpact
    ) -> str:
        """Generate a Recents.md entry"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        
        entry = f"""## {timestamp} - {impact.title}

**Context**: {impact.description}  
**Changes**: `{file_path}`  
**Decision**: {impact.decision or 'N/A'}  
**Status**: {impact.status}

"""
        return entry
    
    def _insert_recent_entry(self, existing_content: str, entry: str) -> str:
        """Insert entry at top of Recents.md"""
        lines = existing_content.split('\n')
        
        # Find where to insert (after the main header)
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('# ') and i == 0:
                # Skip title
                insert_index = i + 1
                # Skip any blank lines after title
                while insert_index < len(lines) and not lines[insert_index].strip():
                    insert_index += 1
                break
        
        # Insert new entry
        lines.insert(insert_index, entry)
        
        return '\n'.join(lines)
    
    async def _read_file(self, file_path: str) -> str:
        """Read file content"""
        if not os.path.exists(file_path):
            # Create new Recents.md if it doesn't exist
            return """# Recent Activity

This file tracks recent significant changes and decisions in the project.

"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""
    
    async def _write_file(self, file_path: str, content: str):
        """Write file content"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
