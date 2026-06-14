import psycopg2
from psycopg2.extras import execute_values
import numpy as np
from typing import List, Dict, Any

CREATE_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id UUID PRIMARY KEY,
    doc_id UUID NOT NULL,
    text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    dense_vector vector(768) NOT NULL,
    metadata JSONB DEFAULT '{}',
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- Drop index if exists to recreate
DROP INDEX IF EXISTS hnsw_idx;
CREATE INDEX hnsw_idx ON document_chunks 
USING hnsw (dense_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS doc_id_idx ON document_chunks (doc_id);
CREATE INDEX IF NOT EXISTS ingested_at_idx ON document_chunks (ingested_at);
"""

class PgVectorIndexer:
    def __init__(self, connection_string: str):
        self.conn_str = connection_string
        self.conn = psycopg2.connect(self.conn_str)
        self._init_db()

    def _init_db(self):
        with self.conn.cursor() as cur:
            cur.execute(CREATE_SCHEMA_SQL)
        self.conn.commit()

    def insert_chunk(self, chunk: Dict[str, Any]):
        query = """
            INSERT INTO document_chunks (chunk_id, doc_id, text, chunk_index, dense_vector, metadata, ingested_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (chunk_id) DO UPDATE SET
                text = EXCLUDED.text,
                dense_vector = EXCLUDED.dense_vector,
                metadata = EXCLUDED.metadata;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (
                chunk["chunk_id"],
                chunk["doc_id"],
                chunk["text"],
                chunk["chunk_index"],
                chunk["dense_vector"], # Must be list/string for pgvector
                psycopg2.extras.Json(chunk["metadata"]),
                chunk.get("ingested_at")
            ))
        self.conn.commit()

    def bulk_insert(self, chunks: List[Dict[str, Any]]):
        query = """
            INSERT INTO document_chunks (chunk_id, doc_id, text, chunk_index, dense_vector, metadata, ingested_at)
            VALUES %s
            ON CONFLICT (chunk_id) DO NOTHING;
        """
        values = [(
            c["chunk_id"], c["doc_id"], c["text"], c["chunk_index"],
            c["dense_vector"], psycopg2.extras.Json(c["metadata"]), c.get("ingested_at")
        ) for c in chunks]
        
        with self.conn.cursor() as cur:
            execute_values(cur, query, values)
        self.conn.commit()

    def dense_search(self, query_vector: List[float], top_k: int = 10, ef_search: int = 100) -> List[Dict]:
        # Using cosine distance operator `<=>`
        query = f"""
            SET hnsw.ef_search = {ef_search};
            SELECT chunk_id, doc_id, text, metadata, 1 - (dense_vector <=> %s::vector) AS score
            FROM document_chunks
            ORDER BY dense_vector <=> %s::vector
            LIMIT %s;
        """
        vec_str = f"[{','.join(map(str, query_vector))}]"
        with self.conn.cursor() as cur:
            cur.execute(query, (vec_str, vec_str, top_k))
            results = cur.fetchall()
            
        columns = ["chunk_id", "doc_id", "text", "metadata", "score"]
        return [dict(zip(columns, r)) for r in results]

    def close(self):
        self.conn.close()
