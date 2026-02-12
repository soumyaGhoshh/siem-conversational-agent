import os
import json
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env before imports
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import elastic_connector
import schema_extractor
from routes import auth, stats, chat, misc
import asyncio
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI(title="SIEM Conversational Agent API")

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc) if os.getenv("DEBUG") == "true" else "An unexpected error occurred."}
    )

# Rate Limiting Middleware (Disabled as per user request)
# @app.middleware("http")
# async def rate_limit_middleware(request: Request, call_next):
#     # Get client IP or use 'global' if behind proxy
#     client_ip = request.client.host if request.client else "unknown"
#     if not global_limiter.is_allowed(client_ip):
#         raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
#     response = await call_next(request)
#     return response

# CORS
origins = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for hackathon ease
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include Routers
app.include_router(auth.router)
app.include_router(stats.router)
app.include_router(chat.router)
app.include_router(misc.router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "SIEM Conversational Agent API is running"}

@app.get("/api/preflight")
def preflight():
    demo = os.getenv("DEMO_MODE", "true").lower() == "true"
    es_ok = elastic_connector.ping()
    creds_ok = bool(os.getenv("ELASTIC_USER")) and bool(os.getenv("ELASTIC_PASSWORD"))
    api_ok = bool(os.getenv("GOOGLE_API_KEY"))
    try:
        m = schema_extractor.get_index_mapping(os.getenv("ALLOWED_INDEXES", "wazuh-alerts-*").split(",")[0])
        schema_ok = bool(m)
    except Exception:
        schema_ok = demo
    
    if demo:
        return {"esOk": True, "credsOk": True, "llmOk": api_ok, "schemaOk": True, "demoMode": True}
        
    return {"esOk": es_ok, "credsOk": creds_ok, "llmOk": api_ok, "schemaOk": schema_ok}

@app.get("/api/schema")
def schema(index: str):
    m = schema_extractor.get_index_mapping(index)
    s = schema_extractor.simplify_mapping(m)
    fields = []
    props = s.get(index, {})
    for k, v in props.items():
        fields.append({"name": k, "type": v})
    return {"index": index, "fields": fields}

# SSE for real-time alerts
@app.get("/api/alerts/stream")
async def stream_alerts(request: Request, index: str = "wazuh-alerts-*", min_level: int = 10):
    async def event_generator():
        last_timestamp = None
        while True:
            # Check if client closed connection
            if await request.is_disconnected():
                break

            try:
                # Query for the latest alert
                query = {
                    "size": 1,
                    "query": {
                        "bool": {
                            "must": [
                                {"range": {"rule.level": {"gte": min_level}}},
                                {"range": {"@timestamp": {"gte": "now-1m"}}}
                            ]
                        }
                    },
                    "sort": [{"@timestamp": {"order": "desc"}}]
                }
                
                res = elastic_connector.execute_query(json.dumps(query), index_pattern=index)
                if res.get("status") == "success" and res.get("data"):
                    hit = res["data"][0]
                    source = hit.get("_source", {})
                    current_ts = source.get("@timestamp")
                    
                    if current_ts != last_timestamp:
                        alert = {
                            "id": hit.get("_id"),
                            "timestamp": current_ts,
                            "description": source.get("rule", {}).get("description", "No description"),
                            "level": source.get("rule", {}).get("level", 0),
                            "agent": source.get("agent", {}).get("name", "unknown")
                        }
                        yield f"data: {json.dumps(alert)}\n\n"
                        last_timestamp = current_ts
            except Exception as e:
                logger.error(f"SSE Error: {e}")
            
            await asyncio.sleep(5) # Poll every 5s instead of 30s, but it's pushed to client

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# SSE for raw log stream
@app.get("/api/logs/stream")
async def stream_logs(request: Request, index: str = "wazuh-alerts-*"):
    async def log_generator():
        last_timestamp = None
        while True:
            if await request.is_disconnected():
                break
            try:
                query = {
                    "size": 5,
                    "query": {"range": {"@timestamp": {"gte": "now-1m"}}},
                    "sort": [{"@timestamp": {"order": "desc"}}]
                }
                res = elastic_connector.execute_query(json.dumps(query), index_pattern=index)
                if res.get("status") == "success" and res.get("data"):
                    # Reverse to show oldest first in this batch
                    for hit in reversed(res["data"]):
                        source = hit.get("_source", {})
                        ts = source.get("@timestamp")
                        if last_timestamp is None or ts > last_timestamp:
                            log_line = f"[{ts}] {source.get('agent', {}).get('name', 'unknown')} -> {source.get('rule', {}).get('description', 'No description')}"
                            yield f"data: {json.dumps({'line': log_line, 'id': hit.get('_id')})}\n\n"
                            last_timestamp = ts
            except Exception as e:
                logger.error(f"Log Stream Error: {e}")
            await asyncio.sleep(2)
    return StreamingResponse(log_generator(), media_type="text/event-stream")

# Note: Audit and Saved Search routes can be added here or moved to separate files
# For now, keeping them simple in api_server.py or moving them to routes if needed.
