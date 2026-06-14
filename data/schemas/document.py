from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4

class RawDocument(BaseModel):
    doc_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str  # "confluence", "sharepoint", "s3", "web"
    content_type: str  # "pdf", "html", "markdown", "docx"
    raw_content: bytes
    metadata: Dict[str, Any]
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

class ProcessedChunk(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    chunk_index: int
    token_count: int
    metadata: Dict[str, Any]
    
class EmbeddedChunk(ProcessedChunk):
    dense_vector: List[float]  # 768-dim from sentence-transformers
    sparse_vector: Dict[int, float]  # SPLADE v2 sparse weights
    bm25_tokens: List[str]  # tokenized for BM25
