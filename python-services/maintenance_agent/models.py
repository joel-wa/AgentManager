"""
Data models for the Maintenance Agent
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Conversation message"""
    role: str  # user, assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ContextSnapshot(BaseModel):
    """Snapshot of conversation context at file change moment"""
    project_id: str
    file_path: str
    change_type: str  # created, modified, deleted
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conversation_summary: str
    key_decisions: List[str] = Field(default_factory=list)
    mentioned_files: List[str] = Field(default_factory=list)


class ChangeImpact(BaseModel):
    """Analysis of file change impact"""
    significance: float  # 0-1
    title: str
    description: str
    decision: Optional[str] = None
    status: str  # In Progress, Completed, etc.
    related_files: List[str] = Field(default_factory=list)


class DuplicateGroup(BaseModel):
    """Group of duplicate/similar files"""
    files: List[str]
    similarity_score: float
    sample_content: Optional[str] = None


class FileCluster(BaseModel):
    """Semantic cluster of related files"""
    topic: str
    files: List[str]
    coherence: float  # 0-1


class OutdatedItem(BaseModel):
    """Outdated content detection"""
    file: str
    reason: str
    confidence: float
    suggested_fix: Optional[str] = None


class Suggestion(BaseModel):
    """Maintenance suggestion"""
    id: str
    project_id: str
    type: str  # merge, outdated, organize, update
    title: str
    description: str
    affected_files: Optional[List[str]] = None
    priority: str = "medium"  # low, medium, high
    status: str = "pending"  # pending, accepted, dismissed, applied
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ExecutionResult(BaseModel):
    """Result of suggestion execution"""
    success: bool
    changes: Optional[List[str]] = None
    error: Optional[str] = None


class MessageContext(BaseModel):
    """Context message from main agent"""
    project_id: str
    role: str
    content: str


class FileChangeEvent(BaseModel):
    """File change notification"""
    project_id: str
    file_path: str
    change_type: str  # created, modified, deleted
