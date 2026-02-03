"""
Persistent storage for maintenance suggestions using SQLite
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from models import Suggestion


class SuggestionStore:
    """Persistent storage for maintenance suggestions"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to .meta/suggestions.db in the maintenance agent directory
            db_path = os.path.join(os.path.dirname(__file__), ".meta", "suggestions.db")
        
        self.db_path = db_path
        
        # Ensure directory exists (skip for in-memory databases)
        if db_path != ':memory:':
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                affected_files TEXT,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_status 
            ON suggestions(project_id, status)
        """)
        conn.commit()
        conn.close()
    
    def save_suggestion(self, suggestion: Suggestion):
        """Save or update suggestion"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO suggestions 
            (id, project_id, type, title, description, affected_files, 
             priority, status, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            suggestion.id,
            suggestion.project_id,
            suggestion.type,
            suggestion.title,
            suggestion.description,
            json.dumps(suggestion.affected_files or []),
            suggestion.priority,
            suggestion.status,
            suggestion.created_at.isoformat(),
            datetime.utcnow().isoformat(),
            json.dumps(suggestion.metadata or {})
        ))
        conn.commit()
        conn.close()
    
    def get_pending_suggestions(self, project_id: str) -> List[Suggestion]:
        """Get all pending suggestions for project"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM suggestions 
            WHERE project_id = ? AND status = 'pending'
            ORDER BY priority DESC, created_at DESC
        """, (project_id,))
        
        suggestions = [self._row_to_suggestion(row) for row in cursor.fetchall()]
        conn.close()
        return suggestions
    
    def get_by_id(self, suggestion_id: str) -> Optional[Suggestion]:
        """Get suggestion by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM suggestions WHERE id = ?
        """, (suggestion_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_suggestion(row)
        return None
    
    def update_status(self, suggestion_id: str, new_status: str):
        """Update suggestion status"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE suggestions 
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (new_status, datetime.utcnow().isoformat(), suggestion_id))
        conn.commit()
        conn.close()
    
    def delete_suggestion(self, suggestion_id: str):
        """Delete suggestion from database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM suggestions WHERE id = ?", (suggestion_id,))
        conn.commit()
        conn.close()
    
    def _row_to_suggestion(self, row: sqlite3.Row) -> Suggestion:
        """Convert database row to Suggestion object"""
        return Suggestion(
            id=row["id"],
            project_id=row["project_id"],
            type=row["type"],
            title=row["title"],
            description=row["description"],
            affected_files=json.loads(row["affected_files"]) if row["affected_files"] else None,
            priority=row["priority"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else None
        )
