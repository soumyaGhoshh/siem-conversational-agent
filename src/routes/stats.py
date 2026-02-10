import json
import logging
from fastapi import APIRouter, Request
import elastic_connector
from .auth import require_auth

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_stats(request: Request, index: str = "wazuh-alerts-*"):
    """Fetch high-level security metrics and aggregations for the dashboard"""
    require_auth(request)
    try:
        # Get total alerts in last 24h
        total_query = {"size": 0, "query": {"range": {"@timestamp": {"gte": "now-24h"}}}}
        total_res = elastic_connector.execute_query(json.dumps(total_query), index_pattern=index)
        
        # Get high severity alerts (level > 10 in Wazuh terms)
        high_query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": "now-24h"}}},
                        {"range": {"rule.level": {"gte": 10}}}
                    ]
                }
            }
        }
        high_res = elastic_connector.execute_query(json.dumps(high_query), index_pattern=index)
        
        # Aggregations for charts and dynamic stats
        aggs_query = {
            "size": 0,
            "aggs": {
                "by_time": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "fixed_interval": "1h"
                    }
                },
                "top_terms": {
                    "terms": {
                        "field": "rule.description",
                        "size": 10
                    }
                },
                "active_agents": {
                    "cardinality": {
                        "field": "agent.id"
                    }
                },
                "top_attacker": {
                    "terms": {
                        "field": "data.srcip",
                        "size": 1
                    }
                },
                "risk_scoring": {
                    "terms": {
                        "field": "agent.name",
                        "size": 5
                    },
                    "aggs": {
                        "score": {
                            "sum": {
                                "field": "rule.level"
                            }
                        }
                    }
                }
            }
        }
        aggs_res = elastic_connector.execute_aggregation(json.dumps(aggs_query), index_pattern=index)
        
        total_count = total_res.get("total_hits", 0) if total_res.get("status") == "success" else 0
        high_count = high_res.get("total_hits", 0) if high_res.get("status") == "success" else 0
        
        # Extract dynamic values from aggregations
        active_agents = aggs_res.get("active_agents", {}).get("value", 0)
        top_attacker_buckets = aggs_res.get("top_attacker", {}).get("buckets", [])
        top_attacker = top_attacker_buckets[0].get("key", "N/A") if top_attacker_buckets else "N/A"
        
        # Extract risk scoring
        risk_buckets = aggs_res.get("risk_scoring", {}).get("buckets", [])
        risk_data = [
            {"entity": b.get("key"), "score": b.get("score", {}).get("value", 0)}
            for b in risk_buckets
        ]
        
        return {
            "totalAlerts": total_count,
            "highSeverity": high_count,
            "activeAgents": active_agents,
            "topAttacker": top_attacker,
            "riskScoring": risk_data,
            "aggregations": aggs_res
        }
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        return {
            "error": str(e), 
            "totalAlerts": 0, 
            "highSeverity": 0, 
            "activeAgents": 0, 
            "topAttacker": "N/A",
            "riskScoring": [],
            "aggregations": {}
        }

@router.get("/alerts/recent")
async def get_recent_alerts(request: Request, index: str = "wazuh-alerts-*", min_level: int = 10):
    """Fetch recent high-severity alerts for proactive alerting"""
    require_auth(request)
    try:
        query = {
            "size": 5,
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
        
        if res.get("status") == "success":
            alerts = []
            for hit in res.get("data", []):
                alerts.append({
                    "id": hit.get("_id", "unknown"),
                    "timestamp": hit.get("@timestamp"),
                    "description": hit.get("rule", {}).get("description", "No description"),
                    "level": hit.get("rule", {}).get("level", 0),
                    "agent": hit.get("agent", {}).get("name", "unknown")
                })
            return alerts
        return []
    except Exception as e:
        logger.error(f"Error in get_recent_alerts: {e}")
        return []
