"""
Content Summarizer
Generates summaries and tags for workspace content
"""

from typing import Tuple, List
import re


class ContentSummarizer:
    """Generates summaries and tags for content"""
    
    def __init__(self, cloud_client=None):
        self.cloud_client = cloud_client
        self.max_content_length = 4000  # Characters to analyze
    
    async def summarize(
        self, 
        content: str, 
        filepath: str
    ) -> Tuple[str, List[str]]:
        """
        Generate summary and tags for content
        Returns (summary, tags)
        """
        # Truncate content if needed
        truncated = content[:self.max_content_length]
        
        # Determine file type
        file_ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
        
        # Try cloud summarization
        if self.cloud_client:
            try:
                summary = await self._cloud_summarize(truncated, filepath, file_ext)
                tags = self._extract_tags(content, file_ext)
                return summary, tags
            except Exception:
                pass
        
        # Fallback to local summarization
        summary = self._local_summarize(truncated, file_ext)
        tags = self._extract_tags(content, file_ext)
        
        return summary, tags
    
    async def _cloud_summarize(
        self, 
        content: str, 
        filepath: str,
        file_ext: str
    ) -> str:
        """Generate summary using cloud AI"""
        prompt = f"""Summarize this {file_ext} file in 1-2 sentences:

File: {filepath}
Content:
{content}

Be concise and capture the main purpose/topic."""

        system = "You are a technical summarizer. Provide brief, accurate summaries."
        
        return await self.cloud_client.generate(prompt, system, max_tokens=150)
    
    def _local_summarize(self, content: str, file_ext: str) -> str:
        """Generate basic summary without AI"""
        lines = content.split("\n")
        non_empty = [l.strip() for l in lines if l.strip()]
        
        # For markdown, use first heading
        if file_ext == "md":
            for line in non_empty:
                if line.startswith("#"):
                    title = line.lstrip("#").strip()
                    return f"Document about: {title}"
        
        # For code, try to find main function/class
        if file_ext in ["py", "js", "ts", "rs"]:
            for line in non_empty:
                if re.match(r"^(def |class |function |fn |pub fn |async fn )", line):
                    return f"Code file containing: {line[:50]}..."
        
        # Default: first non-empty line
        if non_empty:
            return f"{non_empty[0][:100]}..."
        
        return "Empty or minimal content"
    
    def _extract_tags(self, content: str, file_ext: str) -> List[str]:
        """Extract relevant tags from content"""
        tags = []
        content_lower = content.lower()
        
        # Add file type tag
        if file_ext:
            tags.append(file_ext)
        
        # Check for common topics
        topic_keywords = {
            "authentication": ["auth", "login", "password", "jwt", "oauth"],
            "api": ["api", "endpoint", "rest", "graphql", "request"],
            "database": ["database", "sql", "query", "schema", "model"],
            "testing": ["test", "spec", "jest", "pytest", "assert"],
            "configuration": ["config", "settings", "env", "environment"],
            "documentation": ["readme", "docs", "guide", "tutorial"],
            "ui": ["component", "render", "view", "button", "form"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                tags.append(topic)
        
        return tags[:5]  # Limit to 5 tags
