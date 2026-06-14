import torch
from sentence_transformers import SentenceTransformer
import numpy as np
import asyncio
from typing import List

class DenseEncoder:
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", device="cpu", max_batch_size=64, max_wait_ms=10):
        self.device = "cuda" if torch.cuda.is_available() else device
        print(f"Loading dense model {model_name} on {self.device}...")
        self.model = SentenceTransformer(model_name, device=self.device)
        self.model.eval()
        if self.device == "cuda":
            self.model.half() # Half-precision inference
        
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        
        # Warmup
        self._warmup()

    def _warmup(self):
        dummy_text = ["This is a warmup sentence.", "Another warmup sentence for padding handling."]
        self.model.encode(dummy_text, normalize_embeddings=True)
        print("Dense model warmed up.")

    async def encode(self, texts: List[str]) -> np.ndarray:
        # In a real dynamic batching setup, we'd queue these and a background worker would consume them.
        # For simplicity here, we'll encode synchronously.
        return self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        
    async def encode_batch(self, texts: List[str], batch_size: int) -> np.ndarray:
        return self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True, convert_to_numpy=True)
