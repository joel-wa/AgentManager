"""
Maintenance Agent Service
Handles background workspace analysis and maintenance using cloud AI models
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from datetime import datetime
import uuid
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from cloud_client import CloudClient
from analyzer import WorkspaceAnalyzer
from summarizer import ContentSummarizer
from context_tracker import ConversationContext
from file_monitor import FileChangeMonitor
from suggestion_store import SuggestionStore
from recents_updater import RecentsUpdater
from suggestion_executor import SuggestionExecutor
from models import Message, MessageContext, FileChangeEvent, Suggestion as SuggestionModel

app = FastAPI(
    title="Maintenance Agent Service",
    description="Background maintenance agent using cloud AI models",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
cloud_client = CloudClient()
analyzer = WorkspaceAnalyzer()
summarizer = ContentSummarizer(cloud_client)
project_paths = {}  # Store project_id -> workspace_path mapping
context_tracker = ConversationContext()
suggestion_store = SuggestionStore()
recents_updater = RecentsUpdater()
suggestion_executor = SuggestionExecutor(cloud_client)
file_monitor = FileChangeMonitor(
    context_tracker=context_tracker,
    analyzer=analyzer,
    cloud_client=cloud_client,
    suggestion_store=suggestion_store,
    recents_updater=recents_updater
)


class AnalyzeRequest(BaseModel):
    project_id: str
    files: Optional[List[Dict[str, Any]]] = None


class Suggestion(BaseModel):
    id: str
    type: str  # merge, outdated, update
    title: str
    description: str
    affected_files: Optional[List[str]] = None
    priority: str = "medium"


class AnalyzeResponse(BaseModel):
    project_id: str
    health_score: float
    suggestions: List[Suggestion]
    analyzed_at: datetime


class SummarizeRequest(BaseModel):
    filepath: str
    content: str


class SummarizeResponse(BaseModel):
    filepath: str
    summary: str
    tags: List[str]
    generated_at: datetime


class HealthResponse(BaseModel):
    status: str
    cloud_available: bool


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health"""
    cloud_available = await cloud_client.check_availability()
    return HealthResponse(
        status="healthy",
        cloud_available=cloud_available
    )


@app.post("/maintenance/analyze", response_model=AnalyzeResponse)
async def analyze_workspace(request: AnalyzeRequest):
    """
    Analyze workspace and generate maintenance suggestions
    """
    try:
        # Run analysis
        analysis_result = await analyzer.analyze(
            project_id=request.project_id,
            files=request.files or []
        )
        
        # Generate suggestions using cloud AI
        suggestions = await generate_suggestions(analysis_result)
        
        return AnalyzeResponse(
            project_id=request.project_id,
            health_score=analysis_result.get("health_score", 0.8),
            suggestions=suggestions,
            analyzed_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/summarize", response_model=SummarizeResponse)
async def summarize_file(request: SummarizeRequest):
    """
    Generate a summary for a file
    """
    try:
        summary, tags = await summarizer.summarize(
            content=request.content,
            filepath=request.filepath
        )
        
        return SummarizeResponse(
            filepath=request.filepath,
            summary=summary,
            tags=tags,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/readme")
async def update_readme(project_id: str, context: Dict[str, Any]):
    """
    Generate or update project README
    """
    try:
        readme_content = await cloud_client.generate_readme(context)
        return {"content": readme_content, "generated_at": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/shutdown")
async def shutdown():
    """Graceful shutdown endpoint"""
    return {"status": "shutting_down"}


@app.post("/maintenance/context/message")
async def track_message(request: MessageContext):
    """Called by main agent after each message"""
    try:
        logger.info(f"Tracking message for project {request.project_id}: {request.role}")
        context_tracker.add_message(
            request.project_id,
            Message(
                role=request.role,
                content=request.content,
                timestamp=datetime.utcnow()
            )
        )
        return {"status": "tracked"}
    except Exception as e:
        logger.error(f"Error tracking message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/file-change")
async def handle_file_change(request: FileChangeEvent):
    """Called when file changes detected"""
    try:
        logger.info(f"File change detected: {request.file_path} ({request.change_type}) in project {request.project_id}")
        await file_monitor.handle_file_change(
            request.project_id,
            request.file_path,
            request.change_type
        )
        logger.info(f"File change processed successfully for {request.file_path}")
        return {"status": "processing"}
    except Exception as e:
        # Don't fail - maintenance is non-critical
        logger.error(f"Error in file change handler: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/maintenance/suggestions/{project_id}")
async def get_suggestions(project_id: str):
    """Get pending suggestions for a project"""
    try:
        suggestions = suggestion_store.get_pending_suggestions(project_id)
        return {
            "suggestions": [
                {
                    "id": s.id,
                    "type": s.type,
                    "title": s.title,
                    "description": s.description,
                    "affected_files": s.affected_files,
                    "priority": s.priority,
                    "status": s.status,
                    "created_at": s.created_at.isoformat()
                }
                for s in suggestions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/suggestions/{suggestion_id}/accept")
async def accept_suggestion(suggestion_id: str):
    """Accept and execute suggestion"""
    try:
        suggestion = suggestion_store.get_by_id(suggestion_id)
        
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        # Get workspace path for this project
        workspace_path = project_paths.get(suggestion.project_id)
        if not workspace_path:
            raise HTTPException(status_code=400, detail="Project workspace path not found. Please trigger analysis first.")
        
        # Execute
        result = await suggestion_executor.execute(
            suggestion,
            suggestion.project_id,
            workspace_path
        )
        
        # Update status
        if result.success:
            suggestion_store.update_status(suggestion_id, "applied")
        
        return {
            "success": result.success,
            "changes": result.changes,
            "error": result.error
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(suggestion_id: str):
    """Dismiss suggestion (deletes from database)"""
    try:
        suggestion = suggestion_store.get_by_id(suggestion_id)
        
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        suggestion_store.delete_suggestion(suggestion_id)
        logger.info(f"Deleted dismissed suggestion {suggestion_id}")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TriggerRequest(BaseModel):
    workspace_path: str


@app.post("/maintenance/trigger/{project_id}")
async def trigger_maintenance(project_id: str, request: TriggerRequest):
    """Manually trigger full maintenance analysis for a project"""
    try:
        logger.info(f"Manual maintenance trigger for project {project_id}")
        
        # Get project files from file system
        import os
        project_path = request.workspace_path
        
        # Store workspace path for later use
        project_paths[project_id] = project_path
        
        files = []
        if os.path.exists(project_path):
            for root, dirs, filenames in os.walk(project_path):
                # Skip .meta and other hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in filenames:
                    if not filename.startswith('.'):
                        rel_path = os.path.relpath(os.path.join(root, filename), project_path)
                        ext = os.path.splitext(filename)[1][1:] if '.' in filename else ''
                        files.append({
                            "name": filename,
                            "path": rel_path,
                            "extension": ext
                        })
        
        logger.info(f"Found {len(files)} files for analysis")
        
        # Run analysis
        analysis_result = await analyzer.analyze(
            project_id=project_id,
            files=files
        )
        
        # Generate suggestions
        suggestions = await generate_suggestions(analysis_result)
        
        # Save suggestions
        for suggestion in suggestions:
            # Convert to SuggestionModel
            sug_model = SuggestionModel(
                id=suggestion.id,
                project_id=project_id,
                type=suggestion.type,
                title=suggestion.title,
                description=suggestion.description,
                affected_files=suggestion.affected_files,
                priority=suggestion.priority,
                status="pending"
            )
            suggestion_store.save_suggestion(sug_model)
        
        logger.info(f"Generated {len(suggestions)} suggestions")
        
        return {
            "status": "completed",
            "health_score": analysis_result.get("health_score", 0.8),
            "suggestions_generated": len(suggestions),
            "files_analyzed": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error triggering maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_suggestions(analysis: Dict[str, Any]) -> List[Suggestion]:
    """Generate maintenance suggestions from analysis"""
    suggestions = []
    
    # Check for duplicate content
    duplicates = analysis.get("duplicates", [])
    for dup_group in duplicates:
        suggestions.append(Suggestion(
            id=str(uuid.uuid4()),
            type="merge",
            title="Consolidate similar files",
            description=f"Found {len(dup_group)} files with overlapping content",
            affected_files=dup_group,
            priority="medium"
        ))
    
    # Check for outdated content
    outdated = analysis.get("outdated", [])
    for item in outdated:
        suggestions.append(Suggestion(
            id=str(uuid.uuid4()),
            type="outdated",
            title="Outdated content detected",
            description=item.get("reason", "File may contain outdated information"),
            affected_files=[item.get("file")],
            priority="low"
        ))
    
    # Check for organization improvements
    improvements = analysis.get("improvements", [])
    for imp in improvements:
        suggestions.append(Suggestion(
            id=str(uuid.uuid4()),
            type="update",
            title=imp.get("title", "Improvement suggestion"),
            description=imp.get("description", ""),
            affected_files=imp.get("files"),
            priority="low"
        ))
    
    return suggestions


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
