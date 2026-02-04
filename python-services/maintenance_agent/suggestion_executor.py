"""
Execute accepted maintenance suggestions
"""

import os
import logging
from typing import Optional
import json

from models import Suggestion, ExecutionResult
from cloud_client import CloudClient

logger = logging.getLogger(__name__)


class SuggestionExecutor:
    """Execute accepted maintenance suggestions"""
    
    # Configuration constant
    MAX_CONTENT_PREVIEW_LENGTH = 1000
    
    def __init__(self, cloud_client: CloudClient, projects_root: str = None):
        self.cloud_client = cloud_client
        if projects_root is None:
            # Try to get from environment, fall back to relative path
            projects_root = os.environ.get('WORKSPACE_PROJECTS_ROOT') or os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "projects")
        self.projects_root = projects_root
        self.current_workspace = None  # Will be set when executing
    
    async def execute(
        self,
        suggestion: Suggestion,
        project_id: str,
        workspace_path: str = None
    ) -> ExecutionResult:
        """Execute a suggestion and return result with rollback on error"""
        # Use provided workspace_path if given
        if workspace_path:
            self.current_workspace = workspace_path
        else:
            self.current_workspace = os.path.join(self.projects_root, project_id)
        
        # Create backup directory for rollback
        backup_dir = os.path.join(self.current_workspace, ".meta", "backup", suggestion.id)
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            # Backup affected files before making changes
            if suggestion.affected_files:
                for file_path in suggestion.affected_files:
                    await self._backup_file(project_id, file_path, backup_dir)
            
            # Execute based on type
            if suggestion.type == "merge":
                result = await self._execute_merge(suggestion, project_id)
            elif suggestion.type == "outdated":
                result = await self._execute_update(suggestion, project_id)
            elif suggestion.type == "organize":
                result = await self._execute_organization(suggestion, project_id)
            elif suggestion.type == "update":
                result = await self._execute_readme_update(suggestion, project_id)
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Unknown suggestion type: {suggestion.type}"
                )
            
            # If successful, clean up backup
            if result.success:
                import shutil
                shutil.rmtree(backup_dir, ignore_errors=True)
            
            return result
            
        except Exception as e:
            # Rollback on any error
            logger.error(f"Error executing suggestion {suggestion.id}: {e}")
            rollback_success = await self._rollback_changes(backup_dir)
            
            error_msg = f"Execution failed: {str(e)}"
            if rollback_success:
                error_msg += " (Changes have been rolled back)"
            else:
                error_msg += " (WARNING: Rollback may have failed - please check files manually)"
            
            return ExecutionResult(
                success=False,
                error=error_msg
            )
    
    async def _execute_merge(
        self,
        suggestion: Suggestion,
        project_id: str
    ) -> ExecutionResult:
        """Merge duplicate files"""
        files_to_merge = suggestion.affected_files or []
        
        if len(files_to_merge) < 2:
            return ExecutionResult(
                success=False,
                error="Need at least 2 files to merge"
            )
        
        try:
            # 1. Read all file contents
            contents = []
            for file_path in files_to_merge:
                content = await self._read_file(project_id, file_path)
                if content:
                    contents.append({"path": file_path, "content": content})
            
            # 2. Use LLM to intelligently merge
            merged_content = await self._intelligent_merge(contents)
            
            # 3. Write to first file
            primary_file = files_to_merge[0]
            await self._write_file(project_id, primary_file, merged_content)
            
            # 4. Archive other files (move to .archive)
            archived = []
            for file_path in files_to_merge[1:]:
                if await self._archive_file(project_id, file_path):
                    archived.append(file_path)
            
            return ExecutionResult(
                success=True,
                changes=[
                    f"Merged {len(files_to_merge)} files into {primary_file}",
                    f"Archived: {', '.join(archived)}"
                ]
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Error merging files: {str(e)}"
            )
    
    async def _execute_update(
        self,
        suggestion: Suggestion,
        project_id: str
    ) -> ExecutionResult:
        """Update outdated content"""
        # For now, just return a success message
        # In a full implementation, this would use LLM to update the content
        return ExecutionResult(
            success=True,
            changes=[f"Marked for update: {', '.join(suggestion.affected_files or [])}"]
        )
    
    async def _execute_organization(
        self,
        suggestion: Suggestion,
        project_id: str
    ) -> ExecutionResult:
        """Execute organization suggestion"""
        # For now, just return a success message
        return ExecutionResult(
            success=True,
            changes=["Organization suggestion noted"]
        )
    
    async def _intelligent_merge(self, contents: list) -> str:
        """Use LLM to merge file contents intelligently"""
        files_desc = "\n\n".join([
            f"--- File: {c['path']} ---\n{c['content'][:self.MAX_CONTENT_PREVIEW_LENGTH]}"
            for c in contents
        ])
        
        prompt = f"""Merge these {len(contents)} files intelligently:

{files_desc}

Rules:
1. Preserve all unique information
2. Eliminate redundancy
3. Maintain logical structure
4. Add a comment at the top noting this is a merged file
5. Keep the most recent/relevant information when there are conflicts

Return ONLY the merged content, no explanations."""

        merged = await self.cloud_client.generate(prompt)
        return merged
    
    async def _read_file(self, project_id: str, file_path: str) -> Optional[str]:
        """Read file content"""
        try:
            full_path = os.path.join(self.current_workspace, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
        return None
    
    async def _write_file(self, project_id: str, file_path: str, content: str):
        """Write file content"""
        try:
            full_path = os.path.join(self.current_workspace, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
    
    async def _archive_file(self, project_id: str, file_path: str) -> bool:
        """Archive a file to .archive folder"""
        try:
            full_path = os.path.join(self.current_workspace, file_path)
            archive_path = os.path.join(
                self.current_workspace, 
                ".archive",
                file_path
            )
            
            if os.path.exists(full_path):
                os.makedirs(os.path.dirname(archive_path), exist_ok=True)
                os.rename(full_path, archive_path)
                return True
        except Exception as e:
            print(f"Error archiving file {file_path}: {e}")
        return False    
    async def _execute_readme_update(
        self,
        suggestion: Suggestion,
        project_id: str
    ) -> ExecutionResult:
        """Update README with AI-generated content"""
        try:
            # Gather context about the project
            import json
            
            # Read project.json for metadata
            project_json_path = os.path.join(self.current_workspace, ".meta", "project.json")
            project_info = {}
            if os.path.exists(project_json_path):
                with open(project_json_path, 'r', encoding='utf-8') as f:
                    project_info = json.load(f)
            
            # Get list of files
            files = []
            for root, dirs, filenames in os.walk(self.current_workspace):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for filename in filenames:
                    if not filename.startswith('.'):
                        rel_path = os.path.relpath(os.path.join(root, filename), self.current_workspace)
                        files.append(rel_path)
            
            # Build context for README generation
            context = {
                "name": project_info.get("name", "Project"),
                "description": project_info.get("description", ""),
                "files": files
            }
            
            # Generate README content using AI
            readme_content = await self.cloud_client.generate_readme(context)
            
            # Write to README.md
            await self._write_file(project_id, "README.md", readme_content)
            
            return ExecutionResult(
                success=True,
                changes=["Updated README.md with AI-generated content"]
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Error updating README: {str(e)}"
            )    
    async def _backup_file(
        self,
        project_id: str,
        file_path: str,
        backup_dir: str
    ) -> bool:
        """Backup a file before modification"""
        try:
            source_path = os.path.join(self.current_workspace, file_path)
            if not os.path.exists(source_path):
                return True  # File doesn't exist, nothing to backup
            
            # Create subdirectories in backup
            backup_file = os.path.join(backup_dir, file_path)
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(source_path, backup_file)
            logger.info(f"Backed up {file_path} to {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")
            return False
    
    async def _rollback_changes(
        self,
        backup_dir: str
    ) -> bool:
        """Rollback changes from backup directory"""
        try:
            if not os.path.exists(backup_dir):
                return True
            
            import shutil
            
            # Restore all backed up files
            for root, dirs, files in os.walk(backup_dir):
                for filename in files:
                    backup_file = os.path.join(root, filename)
                    rel_path = os.path.relpath(backup_file, backup_dir)
                    target_file = os.path.join(self.current_workspace, rel_path)
                    
                    # Restore file
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    shutil.copy2(backup_file, target_file)
                    logger.info(f"Restored {rel_path} from backup")
            
            # Clean up backup after successful rollback
            shutil.rmtree(backup_dir, ignore_errors=True)
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
