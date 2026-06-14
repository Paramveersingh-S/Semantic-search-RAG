import json
from kafka import KafkaProducer
from typing import Dict, Any
from schemas.document import RawDocument

class KafkaDocumentProducer:
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            retries=5,
            acks='all'
        )

    def produce_document(self, doc: RawDocument, topic: str = "raw-documents"):
        # We need to handle the bytes encoding for raw_content carefully in JSON.
        # So we base64 encode it or process it in memory.
        import base64
        doc_dict = doc.model_dump()
        doc_dict['raw_content'] = base64.b64encode(doc_dict['raw_content']).decode('utf-8')
        doc_dict['ingested_at'] = doc_dict['ingested_at'].isoformat()
        
        future = self.producer.send(
            topic,
            key=doc.content_type,
            value=doc_dict
        )
        return future

    def close(self):
        self.producer.close()
