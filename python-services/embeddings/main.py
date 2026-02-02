"""
Embedding Service
Generates vector embeddings for text content
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from model import EmbeddingModel
from chunker import TextChunker

app = FastAPI(
    title="Embedding Service",
    description="Vector embedding generation for semantic search",
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

# Initialize model (lazy loading)
embedding_model: Optional[EmbeddingModel] = None
text_chunker = TextChunker()


def get_model() -> EmbeddingModel:
    """Get or initialize embedding model"""
    global embedding_model
    if embedding_model is None:
        embedding_model = EmbeddingModel()
    return embedding_model


class EmbedRequest(BaseModel):
    text: str
    chunk: bool = False  # Whether to chunk text before embedding


class EmbedResponse(BaseModel):
    embedding: List[float]
    dimension: int


class BatchEmbedRequest(BaseModel):
    texts: List[str]


class BatchEmbedResponse(BaseModel):
    embeddings: List[List[float]]
    dimension: int


class ChunkRequest(BaseModel):
    text: str
    filepath: Optional[str] = None
    chunk_size: int = 500
    overlap: int = 50


class ChunkResponse(BaseModel):
    chunks: List[str]
    count: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and model status"""
    global embedding_model
    return HealthResponse(
        status="healthy",
        model_loaded=embedding_model is not None,
        model_name=get_model().model_name
    )


@app.post("/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest):
    """
    Generate embedding for text
    """
    try:
        model = get_model()
        
        if request.chunk:
            # Chunk and embed, then average
            chunks = text_chunker.chunk(request.text)
            if chunks:
                embeddings = model.encode_batch(chunks)
                # Average the embeddings
                embedding = [sum(col)/len(col) for col in zip(*embeddings)]
            else:
                embedding = model.encode(request.text)
        else:
            embedding = model.encode(request.text)
        
        return EmbedResponse(
            embedding=embedding,
            dimension=len(embedding)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed/batch", response_model=BatchEmbedResponse)
async def embed_batch(request: BatchEmbedRequest):
    """
    Generate embeddings for multiple texts
    """
    try:
        model = get_model()
        embeddings = model.encode_batch(request.texts)
        
        return BatchEmbedResponse(
            embeddings=embeddings,
            dimension=len(embeddings[0]) if embeddings else 0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chunk", response_model=ChunkResponse)
async def chunk_text(request: ChunkRequest):
    """
    Split text into chunks for embedding
    """
    try:
        chunks = text_chunker.chunk(
            text=request.text,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
            filepath=request.filepath
        )
        
        return ChunkResponse(
            chunks=chunks,
            count=len(chunks)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similarity")
async def compute_similarity(text1: str, text2: str):
    """
    Compute cosine similarity between two texts
    """
    try:
        model = get_model()
        emb1 = model.encode(text1)
        emb2 = model.encode(text2)
        
        # Compute cosine similarity
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a * a for a in emb1) ** 0.5
        norm2 = sum(b * b for b in emb2) ** 0.5
        similarity = dot_product / (norm1 * norm2) if norm1 and norm2 else 0
        
        return {"similarity": similarity}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/shutdown")
async def shutdown():
    """Graceful shutdown endpoint"""
    return {"status": "shutting_down"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
