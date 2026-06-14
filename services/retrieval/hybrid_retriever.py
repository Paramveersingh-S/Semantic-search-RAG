from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import numpy as np

class SearchResult:
    def __init__(self, chunk_id: str, doc_id: str, text: str, score: float, source: str, metadata: Dict = None):
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.text = text
        self.score = score
        self.source = source # "bm25", "dense", "sparse", "hybrid"
        self.metadata = metadata or {}

def reciprocal_rank_fusion(
    rankings: List[List[SearchResult]], 
    k: int = 60,
    weights: Optional[List[float]] = None
) -> List[SearchResult]:
    """
    RRF Score = sum over systems of: weight_i / (k + rank_i)
    """
    if weights is None:
        weights = [1.0] * len(rankings)
        
    rrf_scores = defaultdict(float)
    chunk_map = {}
    
    for system_idx, ranked_results in enumerate(rankings):
        weight = weights[system_idx]
        for rank, result in enumerate(ranked_results):
            # Rank is 0-indexed, usually RRF uses 1-indexed, so we add 1
            rrf_score = weight / (k + rank + 1)
            rrf_scores[result.chunk_id] += rrf_score
            
            if result.chunk_id not in chunk_map:
                chunk_map[result.chunk_id] = result
                
    # Create new SearchResult list with RRF scores
    fused_results = []
    for chunk_id, rrf_score in rrf_scores.items():
        original = chunk_map[chunk_id]
        fused_results.append(SearchResult(
            chunk_id=chunk_id,
            doc_id=original.doc_id,
            text=original.text,
            score=rrf_score,
            source="hybrid_rrf",
            metadata=original.metadata
        ))
        
    fused_results.sort(key=lambda x: x.score, reverse=True)
    return fused_results

def alpha_hybrid_search(
    bm25_results: List[SearchResult],
    dense_results: List[SearchResult],
    alpha: float = 0.5
) -> List[SearchResult]:
    """
    Linear combination alternative to RRF. 0 = pure BM25, 1 = pure dense.
    Requires score normalization to [0, 1].
    """
    def min_max_normalize(results: List[SearchResult]) -> List[SearchResult]:
        if not results:
            return []
        scores = [r.score for r in results]
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            for r in results: r.score = 1.0
        else:
            for r in results: r.score = (r.score - min_s) / (max_s - min_s)
        return results

    norm_bm25 = min_max_normalize(bm25_results)
    norm_dense = min_max_normalize(dense_results)
    
    score_map = defaultdict(float)
    chunk_map = {}
    
    for r in norm_bm25:
        score_map[r.chunk_id] += (1 - alpha) * r.score
        chunk_map[r.chunk_id] = r
        
    for r in norm_dense:
        score_map[r.chunk_id] += alpha * r.score
        if r.chunk_id not in chunk_map:
            chunk_map[r.chunk_id] = r
            
    fused_results = []
    for chunk_id, combined_score in score_map.items():
        original = chunk_map[chunk_id]
        fused_results.append(SearchResult(
            chunk_id=chunk_id,
            doc_id=original.doc_id,
            text=original.text,
            score=combined_score,
            source="hybrid_alpha",
            metadata=original.metadata
        ))
        
    fused_results.sort(key=lambda x: x.score, reverse=True)
    return fused_results
