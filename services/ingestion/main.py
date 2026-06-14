from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from kafka_producer import KafkaDocumentProducer
from typing import Optional, Dict
import sys
import os
import uvicorn
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '../../data'))
from schemas.document import RawDocument

app = FastAPI(title="Ingestion Service")
producer = KafkaDocumentProducer(bootstrap_servers=os.getenv("KAFKA_BROKERS", "kafka:9092"))

@app.post("/ingest")
async def ingest_document(
    source: str = Form(...),
    content_type: str = Form(...),
    metadata: str = Form("{}"),
    file: UploadFile = File(...)
):
    try:
        content = await file.read()
        meta_dict = json.loads(metadata)
        
        doc = RawDocument(
            source=source,
            content_type=content_type,
            raw_content=content,
            metadata=meta_dict
        )
        
        producer.produce_document(doc)
        
        return {"doc_id": doc.doc_id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
