"""
Workspace Analyzer
Analyzes workspace structure and content for maintenance opportunities
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
import hashlib
import httpx

from models import ContextSnapshot, DuplicateGroup, FileCluster, OutdatedItem


class WorkspaceAnalyzer:
    """Analyzes workspace for maintenance suggestions"""
    
    def __init__(self, embeddings_url: str = "http://localhost:8003"):
        self.similarity_threshold = 0.7
        self.embeddings_url = embeddings_url
    
    async def analyze(
        self, 
        project_id: str,
        files: List[Dict[str, Any]],
        context: Optional[ContextSnapshot] = None
    ) -> Dict[str, Any]:
        """
        Analyze workspace and return analysis results with semantic understanding
        """
        result = {
            "project_id": project_id,
            "health_score": 1.0,
            "duplicates": [],
            "semantic_clusters": [],
            "outdated": [],
            "improvements": [],
            "stats": {
                "total_files": len(files),
                "by_type": defaultdict(int)
            }
        }
        
        # Analyze file types
        for file in files:
            ext = file.get("extension", "unknown")
            result["stats"]["by_type"][ext] += 1
        
        # Find potential duplicates (by name similarity)
        result["duplicates"] = self._find_duplicates(files)
        
        # Try semantic duplicate detection via embeddings service
        try:
            semantic_duplicates = await self._find_semantic_duplicates(project_id)
            if semantic_duplicates:
                result["duplicates"].extend(semantic_duplicates)
        except:
            pass  # Fall back to basic detection
        
        # Try semantic clustering
        try:
            clusters = await self._cluster_related_files(project_id)
            if clusters:
                result["semantic_clusters"] = clusters
        except:
            pass
        
        # Find potentially outdated content
        result["outdated"] = self._find_outdated(files)
        
        # Calculate health score
        result["health_score"] = self._calculate_health(result)
        
        # Generate improvement suggestions
        result["improvements"] = self._suggest_improvements(result)
        
        return result
    
    def _find_duplicates(self, files: List[Dict[str, Any]]) -> List[List[str]]:
        """Find files with similar names or content"""
        duplicates = []
        seen_patterns = defaultdict(list)
        
        for file in files:
            name = file.get("name", "")
            # Extract base name without extension
            base = name.rsplit(".", 1)[0].lower()
            
            # Remove common suffixes
            for suffix in ["_v1", "_v2", "_old", "_new", "_backup", "_copy"]:
                base = base.replace(suffix, "")
            
            seen_patterns[base].append(name)
        
        # Return groups with multiple files
        for pattern, names in seen_patterns.items():
            if len(names) > 1:
                duplicates.append(names)
        
        return duplicates
    
    def _find_outdated(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find potentially outdated files"""
        outdated = []
        
        for file in files:
            name = file.get("name", "").lower()
            
            # Check for version indicators
            if any(v in name for v in ["_v1", "_old", "deprecated", "legacy"]):
                outdated.append({
                    "file": file.get("name"),
                    "reason": "File name suggests outdated content"
                })
            
            # Check for old date references
            if any(year in name for year in ["2020", "2021", "2022"]):
                outdated.append({
                    "file": file.get("name"),
                    "reason": "File name contains old date reference"
                })
        
        return outdated
    
    def _calculate_health(self, result: Dict[str, Any]) -> float:
        """Calculate workspace health score (0-1)"""
        score = 1.0
        
        # Deduct for duplicates
        num_duplicates = sum(len(g) - 1 for g in result["duplicates"])
        score -= min(0.2, num_duplicates * 0.02)
        
        # Deduct for outdated files
        num_outdated = len(result["outdated"])
        score -= min(0.2, num_outdated * 0.02)
        
        return max(0.0, score)
    
    def _suggest_improvements(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvement suggestions"""
        improvements = []
        
        # Suggest organizing by file type
        type_stats = result["stats"]["by_type"]
        if len(type_stats) > 3:
            large_groups = [t for t, count in type_stats.items() if count > 5]
            if large_groups:
                improvements.append({
                    "title": "Organize files by type",
                    "description": f"Consider organizing files into folders by type: {', '.join(large_groups)}",
                    "files": None
                })
        
        # Suggest README update if many files
        if result["stats"]["total_files"] > 10:
            improvements.append({
                "title": "Update README",
                "description": "Consider updating README to reflect current project structure",
                "files": ["README.md"]
            })
        
        return improvements
    
    async def _find_semantic_duplicates(
        self,
        project_id: str
    ) -> List[List[str]]:
        """Find semantically similar files using embeddings service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.embeddings_url}/semantic/similar",
                    json={
                        "project_id": project_id,
                        "threshold": self.similarity_threshold
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    similar_pairs = data.get("similar_pairs", [])
                    
                    # Group pairs into clusters
                    clusters = []
                    for pair in similar_pairs:
                        clusters.append([pair.get("file1"), pair.get("file2")])
                    
                    return clusters
        except:
            pass
        
        return []
    
    async def _cluster_related_files(
        self,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """Group files by semantic similarity"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.embeddings_url}/semantic/cluster",
                    json={
                        "project_id": project_id,
                        "num_clusters": "auto"
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("clusters", [])
        except:
            pass
        
        return []
