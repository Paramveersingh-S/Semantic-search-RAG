from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import httpx
import os

router = APIRouter()

INGESTION_SERVICE_URL = os.getenv("INGESTION_SERVICE_URL", "http://ingestion:8000")

@router.post("/ingest")
async def ingest_document(
    source: str = Form(...),
    content_type: str = Form(...),
    metadata: str = Form("{}"),
    file: UploadFile = File(...)
):
    # Validate
    allowed_types = ["pdf", "html", "markdown", "docx"]
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid content type. Allowed: {allowed_types}")
        
    # Forward to ingestion service
    content = await file.read()
    
    try:
        async with httpx.AsyncClient() as client:
            files = {'file': (file.filename, content, file.content_type)}
            data = {
                'source': source,
                'content_type': content_type,
                'metadata': metadata
            }
            resp = await client.post(f"{INGESTION_SERVICE_URL}/ingest", data=data, files=files)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error communicating with ingestion service: {str(e)}")
