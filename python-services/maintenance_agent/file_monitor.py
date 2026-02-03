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
        change_type: str  # created, modified, deleted
    ):
        """Main handler for file change events"""
        try:
            # 1. Capture conversation context
            context = self.context_tracker.capture_context_for_file_change(
                project_id, file_path, change_type
            )
            
            # 2. Analyze change impact
            impact = await self._analyze_change_impact(
                project_id, file_path, change_type, context
            )
            
            # 3. Update Recents.md if significant
            if impact and impact.significance >= 0.7:
                await self.recents_updater.update_recents(
                    project_id, file_path, context, impact
                )
            
            # 4. Check for maintenance opportunities
            suggestions = await self._generate_suggestions_from_change(
                project_id, file_path, context, impact
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
        context: ContextSnapshot
    ) -> Optional[ChangeImpact]:
        """Determine significance of the change"""
        try:
            prompt = f"""Analyze this file change and return a JSON object:

File: {file_path}
Change Type: {change_type}
Recent Conversation: {context.conversation_summary}
Key Decisions: {', '.join(context.key_decisions) if context.key_decisions else 'None'}

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
        context: ContextSnapshot,
        impact: Optional[ChangeImpact]
    ) -> list[Suggestion]:
        """Generate maintenance suggestions based on file change"""
        suggestions = []
        
        try:
            # Check for similar files that might need updates
            similar_files = await self._find_similar_files(project_id, file_path)
            
            if similar_files and len(similar_files) > 0:
                suggestions.append(Suggestion(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    type="update",
                    title=f"Similar files may need updates",
                    description=f"File {file_path} was changed. Consider updating related files: {', '.join(similar_files[:3])}",
                    affected_files=similar_files,
                    priority="low"
                ))
        
        except Exception as e:
            print(f"Error generating suggestions: {e}")
        
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
        except:
            pass
        
        return []
