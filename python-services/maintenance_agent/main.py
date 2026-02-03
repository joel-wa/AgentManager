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

from cloud_client import CloudClient
from analyzer import WorkspaceAnalyzer
from summarizer import ContentSummarizer

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
    uvicorn.run(app, host="0.0.0.0", port=8004)
