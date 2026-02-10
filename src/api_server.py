import os
import logging
from fastapi import FastAPI
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
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

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

# Note: Audit and Saved Search routes can be added here or moved to separate files
# For now, keeping them simple in api_server.py or moving them to routes if needed.
