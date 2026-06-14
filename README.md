# Enterprise Semantic Search & RAG Platform

A production-grade Enterprise Semantic Search and Retrieval-Augmented Generation (RAG) Platform.

## Architecture

![Architecture](https://via.placeholder.com/800x400.png?text=Architecture+Diagram)

## Quickstart

1. Ensure Docker and Docker Compose are installed.
2. Run `docker-compose up -d` to start the infrastructure locally.
3. Access API Gateway at `http://localhost:8000`.
4. MLflow UI at `http://localhost:5000`.

## Modules

- **Ingestion**: FastAPI and Kafka Producer
- **Processing**: PySpark Streaming for cleaning and chunking
- **Embedding**: gRPC server for Dense (sentence-transformers) and Sparse (SPLADE) embeddings
- **Indexer**: Elasticsearch (BM25 + Sparse) and Postgres pgvector (Dense)
- **Retrieval**: Hybrid Search (BM25 + Dense + Sparse) with Reciprocal Rank Fusion (RRF)
- **Reranker**: Cross-Encoder using HuggingFace
- **RAG**: Answer generation using quantized Mistral 7B
- **API Gateway**: FastAPI with caching and rate limiting
