# 🚀 Google Colab GPU Execution Guide

Because the Reranker (Cross-Encoder) and RAG Generator (Mistral-7B) require a heavy GPU, they are designed to be run in Google Colab. 

You can test the heavy inference parts by opening a new Google Colab notebook, switching the Runtime to **T4 GPU**, and running the following cells.

### Cell 1: Clone the Repository & Setup
```python
!git clone https://github.com/Paramveersingh-S/Semantic-search-RAG.git
%cd Semantic-search-RAG
```

### Cell 2: Install Heavy GPU Dependencies
*Note: We don't use the CPU flag here because we want PyTorch to utilize the Colab T4 GPU!*
```python
!pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
!pip install transformers accelerate bitsandbytes sentence-transformers
```

### Cell 3: Test the Cross-Encoder Reranker
```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

print("Loading Cross-Encoder onto GPU...")
device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = AutoTokenizer.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")
model = AutoModelForSequenceClassification.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2").to(device)

query = "What technologies are used in the API Gateway?"
docs = [
    "The API Gateway is built using FastAPI and Python.",
    "PostgreSQL is used for vector storage.",
    "Redis is used for caching responses in the API Gateway layer."
]

features = tokenizer([[query, doc] for doc in docs], padding=True, truncation=True, return_tensors="pt").to(device)
with torch.no_grad():
    scores = model(**features).logits.squeeze(-1)

# Print reranked results
ranked = sorted(zip(scores.cpu().numpy(), docs), reverse=True)
for score, doc in ranked:
    print(f"Score: {score:.2f} | Doc: {doc}")
```

### Cell 4: Test the Mistral RAG Generator (4-bit Quantization)
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

print("Loading Mistral-7B Instruct onto GPU in 4-bit...")
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

model_id = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    quantization_config=quant_config, 
    device_map="auto"
)

# Simulate passing the top retrieved documents into the LLM context
context = ranked[0][1] # Highest scored document from previous cell
prompt = f"Context: {context}\n\nQuestion: What technologies are used in the API Gateway?\nAnswer:"

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=50)

print("\n--- LLM GENERATED ANSWER ---")
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### Next Steps for Full Integration
To fully connect Colab to your Codespaces architecture (so Colab acts as an external GPU worker):
1. Expose your Codespaces API Gateway URL using Ngrok.
2. Inside Colab, write a simple `requests` polling script that listens for tasks from your API Gateway.
3. Have Colab perform the heavy generation and send the JSON response back to your architecture!
