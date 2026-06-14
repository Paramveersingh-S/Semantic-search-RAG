import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Tuple
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../retrieval'))
from hybrid_retriever import SearchResult

class CrossEncoderReranker:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-12-v2", device="cpu", batch_size=32):
        self.device = "cuda" if torch.cuda.is_available() else device
        print(f"Loading cross-encoder {model_name} on {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()
        if self.device == "cuda":
            self.model.half()
            
        self.batch_size = batch_size

    async def rerank(self, query: str, candidates: List[SearchResult], top_k: int = 10) -> List[SearchResult]:
        if not candidates:
            return []
            
        pairs = [(query, doc.text) for doc in candidates]
        
        scores = []
        for i in range(0, len(pairs), self.batch_size):
            batch_pairs = pairs[i:i+self.batch_size]
            
            inputs = self.tokenizer(
                batch_pairs,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                batch_scores = outputs.logits.squeeze(-1).cpu().numpy().tolist()
                
                # If batch size is 1, it might not be a list, ensure it is
                if isinstance(batch_scores, float):
                    batch_scores = [batch_scores]
                    
                scores.extend(batch_scores)
                
        # Update scores and sort
        for i, score in enumerate(scores):
            candidates[i].score = score
            
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:top_k]

    def fine_tune(self, train_pairs: List[Tuple[str, str, float]], mlflow_run_id: str):
        # Implementation for fine tuning using MSE loss or BCE
        pass
