FROM python:3.10-slim
WORKDIR /app
COPY services/api_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install extra dependencies for retrieval & grpc
RUN pip install elasticsearch psycopg2-binary grpcio grpcio-tools numpy
COPY services/api_gateway/ ./
COPY data/schemas/ ./schemas/
COPY services/indexer/ ./indexer/
COPY services/retrieval/ ./retrieval/
COPY services/embedding/proto/ ./proto/
# Compile gRPC
RUN python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/embedding.proto
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
