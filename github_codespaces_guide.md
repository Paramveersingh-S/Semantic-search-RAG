# ☁️ GitHub Codespaces Execution Guide

This guide will walk you through setting up and running the complete Enterprise Semantic Search & RAG Platform within **GitHub Codespaces**. 

Because this project involves a robust microservice architecture (Kafka, PySpark, Elasticsearch, Postgres pgvector, and FastAPI services), running it locally can be incredibly taxing on a standard laptop. GitHub Codespaces provides an isolated cloud container with built-in Docker support, making it the perfect environment.

---

## Step 1: Launch the GitHub Codespace

1. Go to your repository on GitHub: `https://github.com/Paramveersingh-S/Semantic-search-RAG`
2. Click the green **`<> Code`** button.
3. Switch to the **`Codespaces`** tab in the dropdown menu.
4. Click **`Create codespace on main`**.
   *Note: If given the option for machine type, select at least a **4-core, 8GB RAM** instance to handle the memory overhead of Elasticsearch and Spark.*
5. Wait for the environment to build. Your browser will open a web-based VS Code interface.

---

## Step 2: Verify Tooling (Built-in)

Once inside the Codespace terminal, you don't need to install Docker or Python—they are pre-configured. Verify them:

```bash
docker --version
docker-compose --version
python --version
```

---

## Step 3: Boot the Infrastructure

The project utilizes `docker-compose.yml` to orchestrate the entire distributed network.

1. Navigate to the project directory (if not already there):
   ```bash
   cd enterprise-search-rag
   ```
2. Start all services in detached mode:
   ```bash
   docker-compose up -d
   ```
3. **Wait 1-2 minutes.** Heavy services like Elasticsearch and Kafka take time to initialize their JVMs.
4. Check the status of your containers to ensure they are healthy:
   ```bash
   docker ps
   ```

---

## Step 4: Interacting with the Platform

GitHub Codespaces will automatically forward the ports defined in the `docker-compose.yml` file (e.g., `8000` for the API Gateway, `5000` for MLflow). 

In the VS Code interface, look at the **`PORTS`** tab next to your Terminal. You will see Port 8000 listed. GitHub generates a secure, unique URL for your forwarded ports (e.g., `https://<your-codespace-id>-8000.app.github.dev`).

### 1. Check API Health
You can click the globe icon next to Port 8000 in the PORTS tab, or use `curl` directly in the terminal:
```bash
curl http://localhost:8000/v1/health
```
*(Expected output: `{"status": "ok", "service": "api_gateway"}`)*

### 2. Ingest a Test Document
We will ingest the `README.md` file itself to test the pipeline.
```bash
curl -X POST http://localhost:8000/v1/ingest \
  -F "source=github_codespaces" \
  -F "content_type=markdown" \
  -F "file=@README.md"
```
*This uploads the file to the API Gateway, which pushes it to Kafka, where PySpark picks it up, cleans it, chunks it, and passes it to the Embedding service to be indexed in Postgres and Elasticsearch.*

### 3. Perform a Semantic Search
Query the system to test the Hybrid Retrieval and RAG answer generation.
```bash
curl -X POST http://localhost:8000/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What technologies are used in the API Gateway?",
    "top_k": 5,
    "search_mode": "hybrid",
    "rerank": true,
    "generate_answer": true
  }'
```

---

## Step 5: Accessing External UI Dashboards

### MLflow (Experiment Tracking)
1. Go to the **PORTS** tab in the Codespace.
2. Find Port **5000**.
3. Click the **"Open in Browser"** (globe icon) button.
4. You will be routed to the MLflow UI where you can view A/B testing retrieval metrics.

### Elasticsearch (Direct API Access)
1. Find Port **9200** in the **PORTS** tab.
2. You can query the raw indices directly via curl:
   ```bash
   curl http://localhost:9200/_cat/indices?v
   ```

---

## Step 6: Shutting Down

When you are done testing, you can spin down the containers to free up memory or simply let the Codespace spin down on its own.

```bash
docker-compose down
```

*Note: GitHub Codespaces automatically stop after a period of inactivity (usually 30 minutes), so you will not be billed indefinitely if you forget to close the browser tab.*
