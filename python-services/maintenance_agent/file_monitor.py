"""
File change monitoring and handling
"""

import os
from typing import Optional
import httpx
import json

from models import ContextSnapshot, ChangeImpact, Suggestion
from context_tracker import ConversationContext
from analyzer import WorkspaceAnalyzer
from cloud_client import CloudClient
from suggestion_store import SuggestionStore
from recents_updater import RecentsUpdater
import uuid


class FileChangeMonitor:
    """Listen for file changes and trigger maintenance actions"""
    
    def __init__(
        self, 
        context_tracker: ConversationContext,
        analyzer: WorkspaceAnalyzer,
        cloud_client: CloudClient,
        suggestion_store: SuggestionStore,
        recents_updater: RecentsUpdater,
        embeddings_url: str = "http://localhost:8003"
    ):
        self.context_tracker = context_tracker
        self.analyzer = analyzer
        self.cloud_client = cloud_client
        self.suggestion_store = suggestion_store
        self.recents_updater = recents_updater
        self.embeddings_url = embeddings_url
    
    async def handle_file_change(
        self,
        project_id: str,
        file_path: str,
        change_type: str,  # created, modified, deleted
        workspace_path: Optional[str] = None,
        file_content: Optional[str] = None,
        readme_content: Optional[str] = None,
        workspace_structure: Optional[dict] = None
    ):
        """Main handler for file change events"""
        try:
            # 1. Capture conversation context
            context = self.context_tracker.capture_context_for_file_change(
                project_id, file_path, change_type
            )
            
            # 2. Analyze change impact with full context
            impact = await self._analyze_change_impact(
                project_id, file_path, change_type, context,
                file_content, readme_content, workspace_structure
            )
            
            # 3. Update Recents.md if significant
            if impact and impact.significance >= 0.7:
                await self.recents_updater.update_recents(
                    project_id, file_path, context, impact
                )
            
            # 4. Check for maintenance opportunities with enhanced context
            suggestions = await self._generate_suggestions_from_change(
                project_id, file_path, change_type, context, impact,
                file_content, readme_content, workspace_structure
            )
            
            # 5. Queue suggestions for user
            for suggestion in suggestions:
                self.suggestion_store.save_suggestion(suggestion)
                
        except Exception as e:
            print(f"Error handling file change: {e}")
    
    async def _analyze_change_impact(
        self, 
        project_id: str,
        file_path: str,
        change_type: str,
        context: ContextSnapshot,
        file_content: Optional[str] = None,
        readme_content: Optional[str] = None,
        workspace_structure: Optional[dict] = None
    ) -> Optional[ChangeImpact]:
        """Determine significance of the change"""
        try:
            # Build enhanced context
            content_preview = ""
            if file_content:
                content_preview = f"\nFile Content (first 500 chars):\n{file_content[:500]}"
            
            structure_info = ""
            if workspace_structure:
                files = workspace_structure.get('files', [])
                folders = workspace_structure.get('folders', [])
                structure_info = f"\nWorkspace Structure:\n- Folders: {', '.join(folders[:10])}\n- Files: {', '.join(files[:10])}"
            
            readme_info = ""
            if readme_content:
                readme_info = f"\nCurrent README (first 300 chars):\n{readme_content[:300]}"
            
            prompt = f"""Analyze this file change and return a JSON object:

File: {file_path}
Change Type: {change_type}
Recent Conversation: {context.conversation_summary}
Key Decisions: {', '.join(context.key_decisions) if context.key_decisions else 'None'}{content_preview}{structure_info}{readme_info}

Rate significance (0.0-1.0) and provide:
1. title: Short title for this change
2. description: What changed conceptually
3. decision: The key decision made (if any)
4. status: Current status (e.g., "In Progress", "Completed")
5. significance: Float between 0.0 and 1.0

Return ONLY valid JSON in this exact format:
{{
  "significance": 0.8,
  "title": "Example Title",
  "description": "Description of the change",
  "decision": "Key decision or null",
  "status": "In Progress"
}}"""

            response = await self.cloud_client.generate(
                prompt,
                system="You are analyzing workspace changes. Return valid JSON only, no other text."
            )
            
            # Parse JSON response
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.startswith('```'):
                response_clean = response_clean[3:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            data = json.loads(response_clean.strip())
            
            return ChangeImpact(
                significance=float(data.get("significance", 0.5)),
                title=data.get("title", "File Change"),
                description=data.get("description", "File was modified"),
                decision=data.get("decision"),
                status=data.get("status", "In Progress"),
                related_files=[file_path]
            )
            
        except Exception as e:
            print(f"Error analyzing change impact: {e}")
            # Return default impact
            return ChangeImpact(
                significance=0.5,
                title="File Change",
                description=f"{change_type.capitalize()} {file_path}",
                decision=None,
                status="In Progress",
                related_files=[file_path]
            )
    
    async def _generate_suggestions_from_change(
        self,
        project_id: str,
        file_path: str,
        change_type: str,
        context: ContextSnapshot,
        impact: Optional[ChangeImpact],
        file_content: Optional[str] = None,
        readme_content: Optional[str] = None,
        workspace_structure: Optional[dict] = None
    ) -> list[Suggestion]:
        """Generate maintenance suggestions based on file change"""
        suggestions = []
        
        try:
            # Build context for AI
            content_preview = ""
            if file_content:
                content_preview = f"\nChanged File Content:\n{file_content[:1000]}"
            
            structure_info = ""
            if workspace_structure:
                files = workspace_structure.get('files', [])
                folders = workspace_structure.get('folders', [])
                structure_info = f"\nWorkspace:\n- Folders: {', '.join(folders)}\n- Files: {', '.join(files)}"
            
            readme_info = ""
            if readme_content:
                readme_info = f"\nCurrent README:\n{readme_content[:500]}"
            
            # Ask AI for suggestions
            prompt = f"""Analyze this file change and suggest maintenance actions:

File Changed: {file_path}
Change Type: {change_type}{content_preview}{structure_info}{readme_info}

Suggest up to 3 maintenance actions from:
1. Update README - if the change should be reflected in project documentation
2. Move file - if the file would fit better in a different folder
3. Merge files - if this file is similar to existing files
4. Update other files - if related files need corresponding changes

Return ONLY valid JSON array:
[
  {{
    "type": "update|move|merge",
    "title": "Short title",
    "description": "Detailed explanation",
    "affected_files": ["file1.txt", "file2.txt"],
    "priority": "high|medium|low"
  }}
]"""
            
            response = await self.cloud_client.generate(
                prompt,
                system="You are a workspace organization expert. Return valid JSON array only."
            )
            
            # Parse suggestions
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.startswith('```'):
                response_clean = response_clean[3:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            import json
            suggestions_data = json.loads(response_clean.strip())
            
            # Convert to Suggestion objects
            for s in suggestions_data:
                suggestions.append(Suggestion(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    type=s.get('type', 'update'),
                    title=s.get('title', 'Maintenance suggestion'),
                    description=s.get('description', ''),
                    affected_files=s.get('affected_files', [file_path]),
                    priority=s.get('priority', 'medium')
                ))
        
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            import traceback
            traceback.print_exc()
        
        return suggestions
    
    async def _find_similar_files(self, project_id: str, file_path: str) -> list[str]:
        """Find files similar to the changed file"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.embeddings_url}/semantic/find_similar",
                    json={
                        "project_id": project_id,
                        "file_path": file_path,
                        "top_k": 5
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("similar_files", [])
        except Exception as e:
            pass
        
        return []
