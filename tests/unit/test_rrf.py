import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../services/retrieval')))
from hybrid_retriever import reciprocal_rank_fusion, SearchResult

def test_rrf():
    list1 = [SearchResult("chunk1", "doc1", "text", 1.0, "bm25"), SearchResult("chunk2", "doc2", "text", 0.9, "bm25")]
    list2 = [SearchResult("chunk2", "doc2", "text", 1.0, "dense"), SearchResult("chunk1", "doc1", "text", 0.9, "dense")]
    
    fused = reciprocal_rank_fusion([list1, list2])
    
    # chunk2 is rank 1 in list1 and rank 0 in list2
    # chunk1 is rank 0 in list1 and rank 1 in list2
    # They should have the same RRF score if weights are equal
    assert len(fused) == 2
    assert abs(fused[0].score - fused[1].score) < 0.001
