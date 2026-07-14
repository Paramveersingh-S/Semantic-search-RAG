# Semantic Search & RAG Platform

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PySpark](https://img.shields.io/badge/PySpark-3.5.1-E25A1C.svg?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Kafka](https://img.shields.io/badge/Kafka-3.7-231F20.svg?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.13-005571.svg?logo=elasticsearch&logoColor=white)](https://www.elastic.co/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg?logo=postgresql&logoColor=white)](https://postgresql.org/)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E.svg?logo=huggingface&logoColor=black)](https://huggingface.co/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Terraform](https://img.shields.io/badge/Terraform-1.8.0-844FBA.svg?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Google Colab](https://img.shields.io/badge/Google%20Colab-%23F9AB00.svg?logo=googlecolab&logoColor=white)](https://colab.research.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A distributed microservices platform for **Enterprise Semantic Search** and **Retrieval-Augmented Generation (RAG)**. Capable of ingesting millions of documents, indexing them via Hybrid Search (BM25 + Dense Vectors + custom SPLADE v2), and serving sub-100ms LLM-powered answer generation.

</div>

---

## 🏛️ Architecture Flow

```mermaid
graph TD
    User(["User / API Client"])
    API["FastAPI Gateway"]
    Kafka["Kafka Broker"]
    Spark["PySpark Processing"]
    ES[("Elasticsearch Index")]
    PG[("PostgreSQL pgvector")]
    Redis[("Redis Cache")]
    Embed["gRPC Embedding Service"]
    Colab["Remote Colab GPU Worker (Ngrok)"]

    User -- "Search / Ingest" --> API
    API -- "Cache Check" --> Redis
    API -- "Raw Docs" --> Kafka
    Kafka -- "Stream" --> Spark
    Spark -- "Chunks" --> Kafka
    Kafka -- "Batch" --> Embed
    
    Embed -- "Sparse Vectors" --> ES
    Embed -- "Dense Vectors" --> PG
    
    API -- "Encode Query" --> Embed
    API -- "BM25" --> ES
    API -- "HNSW" --> PG
    
    API -- "HTTP POST (Context)" --> Colab
    Colab -- "Mistral-7B Answer" --> API
    API -- "JSON Response" --> User
```

---

## ⚙️ Technical Specifications

This platform is meticulously designed referencing enterprise standards set by Elastic, Pinecone, and leading data architectures:

| Component | Technology | Description |
|-----------|------------|-------------|
| **API Gateway** | FastAPI, Redis, SlowAPI | High-throughput gateway handling rate limiting and request caching. |
| **Streaming Ingestion**| Apache Kafka, PySpark | Real-time scalable document ingestion, cleaning, and semantic chunking. |
| **Embeddings** | gRPC, Sentence-Transformers | Dual-encoder service processing Dense representations and custom SPLADE v2 sparse outputs. Dynamic batching enabled. |
| **Vector Indexing** | PostgreSQL + pgvector | HNSW indexed dense vector storage for precise Approximate Nearest Neighbors (ANN) lookups. |
| **Sparse Indexing** | Elasticsearch | Custom standard analyzers coupled with `rank_features` field types for BM25 and SPLADE retrieval. |
| **Hybrid Search** | Reciprocal Rank Fusion (RRF)| Algorithmic aggregation of Dense, Sparse, and Lexical scores into a single weighted pipeline. |
| **Re-Ranking** | HuggingFace Cross-Encoder | Late-interaction re-ranking (O(n) complexity) improving the final precision bounds. |
| **LLM Engine** | Mistral 7B (Quantized) | 4-bit `bitsandbytes` inference for robust answer generation with verifiable document citations. |
| **Observability** | MLflow, Prometheus | Granular metrics scraping and structured experiment tracking (A/B retrieval testing). |
| **Infrastructure** | Terraform, Kubernetes (EKS)| Cloud-native deployment provisioning via IaC with Argo Rollout canary integrations. |

---

This repository is optimized for isolated cloud-development environments like **GitHub Codespaces** and offloads heavy GPU Generation to **Google Colab**.

👉 **[Read the Step-by-Step GitHub Codespaces Setup Guide here](./github_codespaces_guide.md)**  
👉 **[Read the Heavy GPU Google Colab Guide here](./google_colab_guide.md)**

### Brief Overview of Running the Project

1. **Launch a GitHub Codespace**: Provision a 4-core, 8GB machine directly from the repository.
2. **Boot the Infrastructure**: 
   ```bash
   docker-compose up -d
   ```
   *(Codespaces natively supports Docker in Docker)*
3. **Check Service Health**:
   Wait ~60 seconds for Kafka and Elasticsearch to stabilize.
   ```bash
   curl http://localhost:8000/v1/health
   ```
4. **Ingest a Document**:
   ```bash
   curl -X POST http://localhost:8000/v1/ingest -F "source=manual" -F "content_type=markdown" -F "file=@README.md"
   ```
5. **Search the Knowledge Base**:
   ```bash
   curl -X POST http://localhost:8000/v1/search -H "Content-Type: application/json" -d '{"query": "What is the hybrid search strategy?", "generate_answer": true}'
   ```

---

## 🧪 Testing

A comprehensive test suite is included ensuring chunking stability and mathematical precision of the RRF algorithms.
```bash
# From the project root
pip install pytest
pytest tests/unit/
```

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
