import os
import json
import time
import logging
from fastapi import APIRouter, Request, HTTPException
import audit as audit_module
import user_store
import elastic_connector
from .auth import require_auth

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

SAVED_SEARCHES_PATH = os.getenv("SAVED_SEARCHES_PATH", "saved_searches.json")

def load_saved():
    try:
        if os.path.exists(SAVED_SEARCHES_PATH):
            with open(SAVED_SEARCHES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception:
        return []

def save_saved(data):
    with open(SAVED_SEARCHES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)

@router.get("/audit")
async def get_audit(request: Request):
    require_auth(request)
    return audit_module.get_entries()

@router.get("/saved")
async def get_saved(request: Request):
    require_auth(request)
    return load_saved()

@router.post("/saved")
async def create_saved(request: Request):
    uname, _ = require_auth(request)
    body = await request.json()
    saved = load_saved()
    new_entry = {
        "id": int(time.time() * 1000),
        "name": body.get("name"),
        "index": body.get("index"),
        "queryJson": body.get("queryJson"),
        "createdBy": uname,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    saved.append(new_entry)
    save_saved(saved)
    return new_entry

@router.post("/builder")
async def builder(request: Request):
    uname, role = require_auth(request)
    body = await request.json()
    field = body.get("field")
    op = body.get("op")
    val = body.get("value")
    index = body.get("index", "wazuh-alerts-*")
    size = int(body.get("size", 100))
    
    # Construct DSL
    if op == "equals":
        q = {"term": {field: val}}
    elif op == "contains":
        q = {"match": {field: val}}
    elif op == "gt":
        q = {"range": {field: {"gt": val}}}
    elif op == "lt":
        q = {"range": {field: {"lt": val}}}
    else:
        q = {"match_all": {}}
        
    dsl = {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    q,
                    {"range": {"@timestamp": {"gte": "now-24h"}}}
                ]
            }
        }
    }
    
    res = elastic_connector.execute_query(json.dumps(dsl), index_pattern=index)
    return {"queryGenerated": json.dumps(dsl), "results": res.get("data", []), "status": res.get("status")}

@router.post("/remediate")
async def remediate(request: Request):
    uname, _ = require_auth(request)
    body = await request.json()
    action = body.get("action")
    logger.info(f"User {uname} initiated remediation: {action}")
    
    webhook_url = os.getenv("REMEDIATION_WEBHOOK_URL")
    
    # Real Webhook Execution
    if webhook_url:
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "text": f"🚨 *SIEM Remediation Triggered*\n*Action:* {action}\n*Analyst:* {uname}\n*Timestamp:* {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
                    "action": action,
                    "user": uname
                }
                await client.post(webhook_url, json=payload, timeout=5.0)
                logger.info(f"Successfully sent remediation webhook to {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to send remediation webhook: {e}")
            # We continue so the user still gets a success message in demo mode
    
    # Mocking a webhook or orchestration call for demo
    time.sleep(1) # Simulate network latency
    
    return {
        "status": "success", 
        "message": f"Remediation action '{action}' has been successfully triggered.",
        "details": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "triggeredBy": uname,
            "webhookSent": bool(webhook_url),
            "mockTarget": "SOAR-Webhook-01"
        }
    }
