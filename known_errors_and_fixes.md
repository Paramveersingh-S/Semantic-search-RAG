# 🐛 Known Errors & Troubleshooting Guide

This document is a local-only reference file that tracks issues encountered during development and their respective fixes.

---

## 1. Bitnami Docker Hub Image Deprecation
**Error:** 
`Error response from daemon: failed to resolve reference "docker.io/bitnami/kafka:3.7": docker.io/bitnami/kafka:3.7: not found`

**Root Cause:**
Bitnami has recently removed access to their free, public container images from Docker Hub, migrating them to commercial VMware/Broadcom registries. Standard `bitnami/kafka:latest` or `bitnami/zookeeper:3.9` tags will fail to pull.

**Solution:**
Migrated `docker-compose.yml` away from Bitnami images to official Confluent Inc images (`confluentinc/cp-zookeeper:7.5.0` and `confluentinc/cp-kafka:7.5.0`). Replaced Bitnami's custom `KAFKA_CFG_*` environment variables with standard Apache/Confluent environment configurations.

---

## 2. GitHub Mermaid Rendering Engine Crash
**Error:**
`Unable to render rich display. Could not find a suitable point for the given distance ... graph TD`

**Root Cause:**
GitHub's native Mermaid Markdown parser struggles to render HTML tags (`<br/>`) inside specialized node shapes (like database cylinders `[()]`). It also frequently crashes when calculating coordinates for bidirectional arrows (`<-->`) in dense graphs.

**Solution:**
Simplified the Mermaid graph syntax in `README.md`. Removed all HTML line breaks, used quoted strings for node labels (`Node[("Text")]`), and changed all bidirectional arrows to explicitly labeled unidirectional arrows (`-- "Label" -->`).

---

## 3. Docker Compose Empty Dockerfile Error
**Error:**
`target api_gateway: failed to solve: the Dockerfile cannot be empty`

**Root Cause:**
During the initial project scaffolding phase, placeholder `Dockerfile`s were created using `touch`. When running `docker-compose up -d --build`, Docker attempts to execute these build contexts but crashes because they lack a `FROM` declaration or instructions.

**Solution:**
Populated all 8 microservice Dockerfiles with standard `python:3.10-slim` base images, `pip install` instructions, and generic `CMD ["tail", "-f", "/dev/null"]` entry points for the background modules. 

---

## 4. GitHub Codespaces Disk Exhaustion (Errno 28)
**Error:**
`ERROR: Could not install packages due to an OSError: [Errno 28] No space left on device`

**Root Cause:**
GitHub Codespaces provides a hard limit of 32GB disk space. The `requirements.txt` for the Machine Learning nodes (`embedding`, `rag`, `reranker`) included PyTorch. By default, `pip install torch` downloads the CUDA-compiled version which is roughly ~2.5 GB. Because Docker Compose builds the images concurrently, it attempted to cache over ~8 GB of PyTorch binaries simultaneously, instantly killing the disk space.

**Solution:**
Edited the Dockerfiles for the ML nodes to forcefully install the lightweight CPU-only wheels for PyTorch:
`RUN pip install --no-cache-dir torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu`
This reduced the PyTorch footprint from ~2.5GB to ~250MB per container. Cleaned the broken caches using `docker builder prune -a -f`.
