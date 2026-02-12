import os
import json
import time
import logging
from fastapi import APIRouter, Request, HTTPException
import agent_logic
import schema_extractor
import elastic_connector
from .auth import require_auth

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

AGG_CACHE = {}

def cache_get(key):
    ttl = int(os.getenv("CACHE_TTL_SECONDS", "30"))
    v = AGG_CACHE.get(key)
    if not v:
        return None
    ts, data = v
    if time.time() - ts > ttl:
        return None
    return data

def cache_set(key, data):
    AGG_CACHE[key] = (time.time(), data)

@router.post("/chat")
async def chat(request: Request):
    logger.info("Chat endpoint reached")
    try:
        uname, role = require_auth(request)
    except HTTPException as e:
        logger.warning(f"Auth failed in chat: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected auth error: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"Auth success: {uname} ({role})")
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse request JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")
        
    prompt = body.get("prompt", "")
    index = body.get("index", os.getenv("ALLOWED_INDEXES", "wazuh-alerts-*").split(",")[0])
    
    logger.info(f"Chat request from {uname} ({role}) for index {index}: {prompt[:50]}...")
    
    allowed_env = os.getenv("ALLOWED_INDEXES_ANALYST" if role == "analyst" else "ALLOWED_INDEXES_ADMIN", os.getenv("ALLOWED_INDEXES", "wazuh-alerts-*"))
    allowed_list = [s.strip() for s in allowed_env.split(",") if s.strip()]
    
    if index not in allowed_list:
        logger.warning(f"Index {index} not allowed for role {role}. Allowed: {allowed_list}")
        raise HTTPException(status_code=403, detail="Index not allowed for role")
    
    size = int(body.get("size", 100))
    m = schema_extractor.get_index_mapping(index)
    s = schema_extractor.simplify_mapping(m)
    max_days = 7 if role == "analyst" else int(os.getenv("MAX_LOOKBACK_DAYS", "30"))
    
    try:
        r = agent_logic.process_query(prompt, s, size_limit=size, index_pattern=index, user_name=uname, max_lookback_days=max_days)
    except Exception as e:
        logger.error(f"agent_logic.process_query raised exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

    if not isinstance(r, dict):
        logger.error(f"agent_logic.process_query returned non-dict: {type(r)}")
        raise HTTPException(status_code=500, detail="Internal processing error")
    
    if "error" in r:
        logger.error(f"agent_logic.process_query error: {r['error']}")
        raise HTTPException(status_code=500, detail=r["error"])
    
    agg_field = body.get("aggField")
    aggs = {}
    try:
        histo = {"size": 0, "aggs": {"by_time": {"date_histogram": {"field": "@timestamp", "fixed_interval": "1h"}}}}
        k1 = (index, "histo", json.dumps(histo))
        hcache = cache_get(k1)
        aggs = hcache if hcache else elastic_connector.execute_aggregation(json.dumps(histo), index_pattern=index)
        if not hcache:
            cache_set(k1, aggs)
            
        if agg_field:
            terms = {"size": 0, "aggs": {"top_terms": {"terms": {"field": agg_field, "size": 10}}}}
            k2 = (index, "terms", json.dumps(terms))
            tcache = cache_get(k2)
            taggs = tcache if tcache else elastic_connector.execute_aggregation(json.dumps(terms), index_pattern=index)
            if not tcache:
                cache_set(k2, taggs)
            aggs.update(taggs if isinstance(taggs, dict) else {})
    except Exception as e:
        logger.warning(f"Aggregation failed: {e}")
        pass
        
    return {
        "queryGenerated": r.get("query_generated"), 
        "results": r.get("results"), 
        "aggregations": aggs,
        "analysis": r.get("analysis"),
        "story": r.get("story"),
        "remediation": r.get("remediation"),
        "severity": r.get("severity")
    }

@router.get("/alerts/recent")
async def get_recent_alerts(request: Request, index: str = "wazuh-alerts-*", min_level: int = 10):
    """Fetch recent high-severity alerts for proactive monitoring"""
    require_auth(request)
    try:
        query = {
            "size": 10,
            "query": {
                "bool": {
                    "must": [
                        {"range": {"rule.level": {"gte": min_level}}},
                        {"range": {"@timestamp": {"gte": "now-24h"}}}
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        res = elastic_connector.execute_query(json.dumps(query), index_pattern=index)
        if res.get("status") != "success":
            return []
            
        alerts = []
        for hit in res.get("data", []):
            source = hit.get("_source", {})
            alerts.append({
                "id": hit.get("_id"),
                "timestamp": source.get("@timestamp"),
                "description": source.get("rule", {}).get("description", "No description"),
                "level": source.get("rule", {}).get("level", 0),
                "agent": source.get("agent", {}).get("name", "unknown")
            })
        return alerts
    except Exception as e:
        logger.error(f"Failed to fetch recent alerts: {e}")
        return []
