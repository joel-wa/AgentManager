"""
Text Chunker
Splits text into overlapping chunks for embedding
"""

from typing import List, Optional
import re


class TextChunker:
    """Splits text into chunks suitable for embedding"""
    
    def __init__(self, default_chunk_size: int = 500, default_overlap: int = 50):
        self.default_chunk_size = default_chunk_size
        self.default_overlap = default_overlap
    
    def chunk(
        self,
        text: str,
        chunk_size: int = None,
        overlap: int = None,
        filepath: Optional[str] = None
    ) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks
            filepath: Optional filepath for smart chunking
            
        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.default_chunk_size
        overlap = overlap or self.default_overlap
        
        if not text or not text.strip():
            return []
        
        # Determine chunking strategy based on file type
        if filepath:
            ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
            if ext == "md":
                return self._chunk_markdown(text, chunk_size, overlap)
            elif ext in ["py", "js", "ts", "rs", "go", "java"]:
                return self._chunk_code(text, chunk_size, overlap)
        
        # Default: sentence-based chunking
        return self._chunk_by_sentences(text, chunk_size, overlap)
    
    def _chunk_by_sentences(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: int
    ) -> List[str]:
        """Chunk text by sentence boundaries"""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))
                
                # Start new chunk with overlap
                overlap_text = " ".join(current_chunk)[-overlap:] if overlap else ""
                current_chunk = [overlap_text] if overlap_text else []
                current_size = len(overlap_text)
            
            current_chunk.append(sentence)
            current_size += sentence_size + 1  # +1 for space
        
        # Don't forget last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _chunk_markdown(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: int
    ) -> List[str]:
        """Chunk markdown by sections"""
        # Split by headers
        sections = re.split(r'\n(?=#)', text)
        
        chunks = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            if len(section) <= chunk_size:
                chunks.append(section)
            else:
                # Section too long, chunk by paragraphs
                paragraphs = section.split("\n\n")
                current_chunk = []
                current_size = 0
                
                for para in paragraphs:
                    para_size = len(para)
                    
                    if current_size + para_size > chunk_size and current_chunk:
                        chunks.append("\n\n".join(current_chunk))
                        current_chunk = []
                        current_size = 0
                    
                    current_chunk.append(para)
                    current_size += para_size + 2
                
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
        
        return chunks
    
    def _chunk_code(
        self, 
        text: str, 
        chunk_size: int, 
        overlap: int
    ) -> List[str]:
        """Chunk code by function/class boundaries"""
        # Simple heuristic: split on blank lines or function definitions
        patterns = [
            r'\n\n(?=def |class |fn |function |pub fn |async fn )',  # Python/Rust/JS
            r'\n\n(?=\w)',  # Blank line followed by non-whitespace
        ]
        
        for pattern in patterns:
            sections = re.split(pattern, text)
            if len(sections) > 1:
                break
        else:
            sections = [text]
        
        chunks = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            if len(section) <= chunk_size:
                chunks.append(section)
            else:
                # Split by lines if still too long
                lines = section.split("\n")
                current_chunk = []
                current_size = 0
                
                for line in lines:
                    line_size = len(line)
                    
                    if current_size + line_size > chunk_size and current_chunk:
                        chunks.append("\n".join(current_chunk))
                        # Keep some overlap
                        current_chunk = current_chunk[-2:] if len(current_chunk) > 2 else []
                        current_size = sum(len(l) for l in current_chunk)
                    
                    current_chunk.append(line)
                    current_size += line_size + 1
                
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
        
        return chunks
