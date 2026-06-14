from typing import List, Any
import tiktoken
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../retrieval'))
from hybrid_retriever import SearchResult

RAG_SYSTEM_PROMPT = """You are an expert enterprise search assistant. 
Answer questions based ONLY on the provided context documents.
If the answer is not in the context, say "I don't have enough information to answer this."
Always cite your sources using [Doc N] notation.
Be concise, accurate, and professional."""

def build_rag_prompt(
    query: str,
    retrieved_chunks: List[SearchResult],
    max_context_tokens: int = 3000
) -> str:
    encoder = tiktoken.get_encoding("cl100k_base")
    
    context_parts = []
    current_tokens = 0
    
    for i, chunk in enumerate(retrieved_chunks):
        doc_num = i + 1
        source = chunk.metadata.get("source", chunk.source) if chunk.metadata else chunk.source
        
        part = f"[Doc {doc_num}] Source: {source}\n{chunk.text}\n"
        part_tokens = len(encoder.encode(part))
        
        if current_tokens + part_tokens > max_context_tokens:
            break
            
        context_parts.append(part)
        current_tokens += part_tokens
        
    context_str = "\n".join(context_parts)
    
    final_prompt = f"""{RAG_SYSTEM_PROMPT}

Context:
{context_str}

Question: {query}
Answer:"""

    return final_prompt
