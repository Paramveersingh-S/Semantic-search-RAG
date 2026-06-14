from elasticsearch import Elasticsearch, helpers
from typing import List, Dict, Any

INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 4,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "english_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "english_stop", "english_stemmer", "asciifolding"]
                }
            },
            "filter": {
                "english_stop": {"type": "stop", "stopwords": "_english_"},
                "english_stemmer": {"type": "stemmer", "language": "english"}
            }
        }
    },
    "mappings": {
        "properties": {
            "chunk_id": {"type": "keyword"},
            "doc_id": {"type": "keyword"},
            "text": {
                "type": "text",
                "analyzer": "english_analyzer",
                "term_vector": "with_positions_offsets"
            },
            "sparse_vector": {
                "type": "rank_features"
            },
            "metadata": {"type": "object", "dynamic": True},
            "ingested_at": {"type": "date"}
        }
    }
}

class ElasticsearchIndexer:
    def __init__(self, hosts: List[str] = ["http://localhost:9200"]):
        self.es = Elasticsearch(hosts)

    def create_index(self, index_name: str, mapping: Dict = INDEX_MAPPING):
        if not self.es.indices.exists(index=index_name):
            self.es.indices.create(index=index_name, body=mapping)
            print(f"Created index {index_name}")

    def index_document(self, index_name: str, chunk: Dict[str, Any]):
        # convert integer keys in sparse_vector to strings for ES rank_features
        if "sparse_vector" in chunk:
            chunk["sparse_vector"] = {str(k): v for k, v in chunk["sparse_vector"].items() if v > 0}
            
        self.es.index(index=index_name, id=chunk["chunk_id"], document=chunk)

    def bulk_index(self, index_name: str, chunks: List[Dict[str, Any]], batch_size=500):
        actions = []
        for chunk in chunks:
            if "sparse_vector" in chunk:
                chunk["sparse_vector"] = {str(k): v for k, v in chunk["sparse_vector"].items() if v > 0}
            
            action = {
                "_index": index_name,
                "_id": chunk["chunk_id"],
                "_source": chunk
            }
            actions.append(action)
            
        helpers.bulk(self.es, actions, chunk_size=batch_size)

    def bm25_search(self, index_name: str, query: str, top_k: int = 10, filters: Dict = None) -> List[Dict]:
        es_query = {
            "bool": {
                "must": [
                    {"match": {"text": query}}
                ]
            }
        }
        if filters:
            for k, v in filters.items():
                es_query["bool"]["filter"] = es_query["bool"].get("filter", []) + [{"term": {f"metadata.{k}": v}}]
                
        res = self.es.search(index=index_name, query=es_query, size=top_k)
        return res['hits']['hits']

    def sparse_search(self, index_name: str, sparse_query: Dict[int, float], top_k: int = 10) -> List[Dict]:
        should_clauses = []
        for token_id, weight in sparse_query.items():
            should_clauses.append({
                "rank_feature": {
                    "field": f"sparse_vector.{token_id}",
                    "boost": weight
                }
            })
            
        es_query = {
            "bool": {
                "should": should_clauses
            }
        }
        res = self.es.search(index=index_name, query=es_query, size=top_k)
        return res['hits']['hits']
