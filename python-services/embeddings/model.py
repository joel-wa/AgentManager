"""
Embedding Model
Loads and manages the sentence transformer model
"""

from typing import List
import os


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", 
            "all-MiniLM-L6-v2"
        )
        self._model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            print(f"Loaded embedding model: {self.model_name}")
        except ImportError:
            print("Warning: sentence-transformers not installed. Using fallback.")
            self._model = None
        except Exception as e:
            print(f"Warning: Could not load model: {e}. Using fallback.")
            self._model = None
    
    def encode(self, text: str) -> List[float]:
        """Encode a single text to embedding vector"""
        if self._model is not None:
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            # Fallback: simple hash-based embedding (for testing)
            return self._fallback_encode(text)
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts to embedding vectors"""
        if self._model is not None:
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
        else:
            return [self._fallback_encode(t) for t in texts]
    
    def _fallback_encode(self, text: str, dim: int = 384) -> List[float]:
        """
        Fallback encoding when model not available
        Creates deterministic pseudo-embeddings for testing
        """
        import hashlib
        
        # Create deterministic seed from text
        hash_bytes = hashlib.sha256(text.encode()).digest()
        
        # Generate pseudo-random embedding
        embedding = []
        for i in range(dim):
            byte_idx = i % len(hash_bytes)
            val = (hash_bytes[byte_idx] + i) / 255.0 - 0.5
            embedding.append(val)
        
        # Normalize
        norm = sum(v * v for v in embedding) ** 0.5
        if norm > 0:
            embedding = [v / norm for v in embedding]
        
        return embedding
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        if self._model is not None:
            return self._model.get_sentence_embedding_dimension()
        return 384  # Default dimension
