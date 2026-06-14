from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import hashlib
import time
import os
import httpx
import grpc
from proto import embedding_pb2, embedding_pb2_grpc
from indexer.pgvector_indexer import PgVectorIndexer
from indexer.elasticsearch_indexer import ElasticsearchIndexer
from retrieval.hybrid_retriever import reciprocal_rank_fusion, SearchResult

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    search_mode: str = "hybrid" # hybrid, bm25, dense, sparse
    rerank: bool = True
    generate_answer: bool = True
    filters: Optional[Dict[str, Any]] = None
    stream: bool = False

@router.post("/search")
async def search_endpoint(request: Request, payload: SearchRequest):
    # Rate limit check can be done via slowapi here
    
    # Check cache
    redis_client = request.app.state.redis
    cache_key = f"search:{hashlib.md5(payload.model_dump_json().encode()).hexdigest()}"
    cached = await redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
        
    start_time = time.time()
    
    # 1. Get query embedding
    try:
        with grpc.insecure_channel('embedding:50051') as channel:
            stub = embedding_pb2_grpc.EmbeddingServiceStub(channel)
            emb_resp = stub.EncodeDense(embedding_pb2.EncodeDenseRequest(texts=[payload.query], model_name="BAAI/bge-large-en-v1.5"))
            query_vector = list(emb_resp.vectors[0].values)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding service failed: {e}")
    
    # 2. Query Postgres
    try:
        pg_indexer = PgVectorIndexer("postgresql://admin:secret@postgres:5432/searchdb")
        dense_hits = pg_indexer.dense_search(query_vector, top_k=payload.top_k)
        dense_results = [SearchResult(chunk_id=h["chunk_id"], doc_id=h["doc_id"], text=h["text"], score=h["score"], source="dense") for h in dense_hits]
        pg_indexer.close()
    except Exception as e:
        dense_results = []
    
    # 3. Query Elasticsearch
    try:
        es_indexer = ElasticsearchIndexer(["http://elasticsearch:9200"])
        sparse_hits = es_indexer.bm25_search("document_chunks", payload.query, top_k=payload.top_k)
        sparse_results = [SearchResult(chunk_id=h["_id"], doc_id=h["_source"]["doc_id"], text=h["_source"]["text"], score=h["_score"], source="sparse") for h in sparse_hits]
    except Exception as e:
        sparse_results = []
    
    # 4. Hybrid Fusion
    fused_results = reciprocal_rank_fusion([dense_results, sparse_results], k=60, weights=[0.7, 0.3])
    top_results = fused_results[:payload.top_k]
    
    context_texts = [res.text for res in top_results]
    
    # 5. Forward to RAG Worker
    rag_url = os.getenv("RAG_WORKER_URL")
    answer = None
    if rag_url and payload.generate_answer:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                worker_payload = {
                    "query": payload.query,
                    "context": context_texts
                }
                res = await client.post(f"{rag_url}/generate", json=worker_payload)
                if res.status_code == 200:
                    answer = res.json().get("answer")
                else:
                    answer = f"Error from RAG Worker: {res.text}"
        except Exception as e:
            answer = f"Failed to reach RAG worker: {str(e)}"
    elif payload.generate_answer:
        answer = "RAG_WORKER_URL not configured. Returning top context only."
    
    response_data = {
        "query": payload.query,
        "answer": answer,
        "results": [{"chunk_id": r.chunk_id, "text": r.text, "score": r.score, "source": r.source} for r in top_results],
        "latency": {"total_ms": (time.time() - start_time) * 1000},
        "search_mode": payload.search_mode
    }
    
    # Cache result for 300 seconds
    await redis_client.setex(cache_key, 300, json.dumps(response_data))
    
    return response_data
