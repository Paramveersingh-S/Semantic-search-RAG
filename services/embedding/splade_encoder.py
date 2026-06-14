import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForMaskedLM
from typing import List, Dict

class SPLADEv2Encoder(nn.Module):
    def __init__(self, model_name="distilbert-base-uncased", device="cpu"):
        super().__init__()
        self.device = "cuda" if torch.cuda.is_available() else device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForMaskedLM.from_pretrained(model_name).to(self.device)
        self.model.eval()
        if self.device == "cuda":
            self.model.half()
            
    def forward(self, input_ids, attention_mask):
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits  # [B, L, V]
            
            # SPLADE activation: log(1 + ReLU(logits))
            activated = torch.log(1 + torch.relu(logits))
            
            # Max pool over sequence dimension (ignoring padding)
            mask_expanded = attention_mask.unsqueeze(-1).expand(activated.size())
            activated = activated * mask_expanded
            sparse_vec, _ = torch.max(activated, dim=1)
            
            return sparse_vec  # [B, V]

    def encode(self, texts: List[str], top_k: int = 128) -> List[Dict[int, float]]:
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        sparse_vecs = self.forward(inputs["input_ids"], inputs["attention_mask"])
        
        results = []
        for vec in sparse_vecs:
            # Get non-zero elements
            indices = torch.nonzero(vec).squeeze(-1)
            values = vec[indices]
            
            # Filter top_k
            if len(values) > top_k:
                top_values, top_indices_idx = torch.topk(values, top_k)
                top_indices = indices[top_indices_idx]
            else:
                top_values = values
                top_indices = indices
                
            sparse_dict = {int(idx.item()): float(val.item()) for idx, val in zip(top_indices, top_values)}
            results.append(sparse_dict)
            
        return results

    def decode_sparse(self, sparse_vec: Dict[int, float]) -> Dict[str, float]:
        decoded = {}
        for token_id, weight in sparse_vec.items():
            token_str = self.tokenizer.decode([token_id])
            decoded[token_str] = weight
        return decoded
