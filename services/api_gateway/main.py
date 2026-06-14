from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis.asyncio as redis
import os

from routers import search, ingest, health

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Enterprise Search API Gateway")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Redis for caching
redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
app.state.redis = redis.from_url(redis_url)

# Include routers
app.include_router(search.router, prefix="/v1")
app.include_router(ingest.router, prefix="/v1")
app.include_router(health.router, prefix="/v1")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
