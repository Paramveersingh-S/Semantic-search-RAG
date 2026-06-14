import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from typing import AsyncGenerator, List, Dict
import re
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../retrieval'))
from hybrid_retriever import SearchResult

class RAGAnswerGenerator:
    def __init__(self, model_name="mistralai/Mistral-7B-Instruct-v0.2", quantize=True):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading LLM {model_name} on {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        if quantize and self.device == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto"
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)
            if self.device == "cuda":
                self.model.half()

    async def generate(self, prompt: str, stream: bool = False) -> AsyncGenerator[str, None]:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Simple synchronous generation for now; in a real app use TextIteratorStreamer
        # for proper streaming output
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.1,
            top_p=0.9,
            repetition_penalty=1.1,
            do_sample=True
        )
        
        generated_text = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        if stream:
            # Simulate streaming by yielding chunks
            words = generated_text.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.01)
        else:
            yield generated_text

    def extract_citations(self, answer: str, chunks: List[SearchResult]) -> List[Dict]:
        citations = []
        # Find all [Doc N] references
        matches = re.finditer(r'\[Doc (\d+)\]', answer)
        doc_indices = set(int(m.group(1)) for m in matches)
        
        for idx in doc_indices:
            # doc_num is 1-indexed in prompt
            list_idx = idx - 1
            if 0 <= list_idx < len(chunks):
                chunk = chunks[list_idx]
                citations.append({
                    "doc_id": chunk.doc_id,
                    "chunk_id": chunk.chunk_id,
                    "source": chunk.metadata.get("source", chunk.source) if chunk.metadata else chunk.source,
                    "reference": f"[Doc {idx}]"
                })
                
        return citations
