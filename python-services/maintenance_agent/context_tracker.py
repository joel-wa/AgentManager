"""
Conversation context tracking for maintenance agent
"""

from typing import Dict, List
from datetime import datetime
import re

from models import Message, ContextSnapshot


class ConversationContext:
    """Track conversation history relevant to file changes"""
    
    def __init__(self):
        self.conversations: Dict[str, List[Message]] = {}  # project_id -> messages
        self.file_change_contexts: Dict[str, ContextSnapshot] = {}  # file_path -> snapshot
        self.max_messages_per_project = 50
    
    def add_message(self, project_id: str, message: Message):
        """Called by main agent after each message"""
        if project_id not in self.conversations:
            self.conversations[project_id] = []
        
        self.conversations[project_id].append(message)
        
        # Keep last N messages per project
        if len(self.conversations[project_id]) > self.max_messages_per_project:
            self.conversations[project_id] = self.conversations[project_id][-self.max_messages_per_project:]
    
    def capture_context_for_file_change(
        self, 
        project_id: str, 
        file_path: str,
        change_type: str
    ) -> ContextSnapshot:
        """Capture conversation context at file change moment"""
        recent_messages = self.conversations.get(project_id, [])[-10:]  # Last 10
        
        snapshot = ContextSnapshot(
            project_id=project_id,
            file_path=file_path,
            change_type=change_type,
            timestamp=datetime.utcnow(),
            conversation_summary=self._summarize_messages(recent_messages),
            key_decisions=self._extract_decisions(recent_messages),
            mentioned_files=self._extract_file_mentions(recent_messages)
        )
        
        self.file_change_contexts[file_path] = snapshot
        return snapshot
    
    def _summarize_messages(self, messages: List[Message]) -> str:
        """Summarize conversation leading to change"""
        if not messages:
            return "No recent conversation context"
        
        # Simple summarization: concatenate last few messages
        summary_parts = []
        for msg in messages[-5:]:  # Last 5 messages
            role_label = "User" if msg.role == "user" else "Assistant"
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"{role_label}: {content_preview}")
        
        return " | ".join(summary_parts)
    
    def _extract_decisions(self, messages: List[Message]) -> List[str]:
        """Extract key decisions from messages"""
        decisions = []
        decision_patterns = [
            r"(?:decided to|will use|choosing|going with|implementing|using)\s+(.+?)(?:\.|,|\n|$)",
            r"(?:let's|we'll|I'll)\s+(use|implement|create|add|update)\s+(.+?)(?:\.|,|\n|$)"
        ]
        
        for msg in messages:
            for pattern in decision_patterns:
                matches = re.finditer(pattern, msg.content, re.IGNORECASE)
                for match in matches:
                    decision = match.group(0).strip()
                    if len(decision) < 150:  # Keep it concise
                        decisions.append(decision)
        
        return decisions[-5:]  # Return last 5 decisions
    
    def _extract_file_mentions(self, messages: List[Message]) -> List[str]:
        """Extract mentioned file paths"""
        files = []
        # Pattern for file paths
        file_patterns = [
            r'[\w\-/]+\.(?:py|js|tsx?|rs|md|json|yaml|yml|toml)',
            r'`([^`]+\.[a-z]{2,4})`'
        ]
        
        for msg in messages:
            for pattern in file_patterns:
                matches = re.finditer(pattern, msg.content, re.IGNORECASE)
                for match in matches:
                    file_path = match.group(1) if match.lastindex else match.group(0)
                    if file_path not in files:
                        files.append(file_path)
        
        return files[-10:]  # Return last 10 mentioned files
