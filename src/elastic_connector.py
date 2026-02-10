from elasticsearch import Elasticsearch
import json
import os
import logging

# Configuration
ELASTIC_URL = os.getenv("ELASTIC_URL", "https://localhost:9200")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"
REQUEST_TIMEOUT = int(os.getenv("ELASTIC_REQUEST_TIMEOUT", "20"))
ALLOWED_INDEXES = [s.strip() for s in os.getenv("ALLOWED_INDEXES", "wazuh-alerts-*").split(",") if s.strip()]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
logger.info(f"ELASTIC_CONNECTOR: DEMO_MODE={DEMO_MODE}")

def get_client():
    if not ELASTIC_URL:
        raise ValueError("ELASTIC_URL environment variable is not set.")
    if not ELASTIC_USER or not ELASTIC_PASSWORD:
        raise ValueError("ELASTIC_USER/ELASTIC_PASSWORD environment variables are not set.")
    return Elasticsearch(
        ELASTIC_URL,
        basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
        verify_certs=VERIFY_SSL,
        ssl_show_warn=not VERIFY_SSL
    )

def ping(timeout=5):
    try:
        client = get_client()
        return bool(client.ping(request_timeout=timeout))
    except Exception:
        return DEMO_MODE

def get_mock_data(size=5):
    import random
    from datetime import datetime, timedelta
    
    mock_alerts = []
    actions = ["File access", "Login success", "Login failure", "Privilege escalation", "Malware detected"]
    agents = ["web-server-01", "db-primary", "workstation-hr-02", "firewall-hq"]
    src_ips = ["192.168.1.50", "10.0.0.120", "172.16.5.10", "8.8.8.8"]
    
    for i in range(size):
        level = random.randint(3, 15)
        mock_alerts.append({
            "@timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat(),
            "rule": {
                "level": level,
                "description": f"Mock Alert: {random.choice(actions)}",
                "id": str(random.randint(1000, 9999)),
                "groups": ["mock", "security"]
            },
            "agent": {
                "id": f"00{random.randint(1,9)}",
                "name": random.choice(agents),
                "ip": "10.0.0.5"
            },
            "data": {
                "srcip": random.choice(src_ips),
                "dstport": random.choice([80, 443, 22, 3389])
            },
            "manager": {"name": "wazuh-manager"},
            "id": f"mock-{i}"
        })
    return mock_alerts

def execute_query(query_dsl, index_pattern="wazuh-alerts-*", size_limit=100):
    """
    Executes a raw DSL query against Elasticsearch.
    """
    try:
        client = get_client()
        # Ensure query is a dict
        if isinstance(query_dsl, str):
            query_dsl = json.loads(query_dsl)
        if not isinstance(query_dsl, dict):
            raise ValueError("Query DSL must be a JSON object.")

        if "size" not in query_dsl or not isinstance(query_dsl.get("size"), int):
            query_dsl["size"] = size_limit
        else:
            query_dsl["size"] = min(query_dsl["size"], size_limit)
            
        if index_pattern not in ALLOWED_INDEXES:
            raise ValueError("Index not allowed")
        logger.info(f"Executing query on {index_pattern} with size {query_dsl['size']}")
        response = client.search(index=index_pattern, body=query_dsl, request_timeout=REQUEST_TIMEOUT)
        
        hits = response.get('hits', {}).get('hits', [])
        total = response.get('hits', {}).get('total', {}).get('value', 0)
        
        return {
            "status": "success",
            "total_hits": total,
            "data": [hit.get('_source', {}) for hit in hits]
        }
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        if DEMO_MODE:
            logger.info("DEMO_MODE active: Returning mock data")
            mock_data = get_mock_data(size=10)
            return {
                "status": "success",
                "total_hits": len(mock_data),
                "data": mock_data,
                "is_mock": True
            }
        return {
            "status": "error",
            "error": str(e)
        }

def execute_aggregation(aggs_dsl, index_pattern="wazuh-alerts-*"):
    try:
        client = get_client()
        if isinstance(aggs_dsl, str):
            aggs_dsl = json.loads(aggs_dsl)
        if not isinstance(aggs_dsl, dict):
            raise ValueError("Aggregation DSL must be a JSON object.")
        if index_pattern not in ALLOWED_INDEXES:
            raise ValueError("Index not allowed")
        logger.info(f"Executing aggregation on {index_pattern}")
        response = client.search(index=index_pattern, body=aggs_dsl, request_timeout=REQUEST_TIMEOUT)
        return response.get('aggregations', {})
    except Exception as e:
        logger.error(f"Aggregation execution failed: {e}")
        if DEMO_MODE:
            logger.info("DEMO_MODE active: Returning mock aggregations")
            # Simple mock aggregations for dashboard
            return {
                "active_agents": {"value": 4},
                "top_attacker": {"buckets": [{"key": "192.168.1.50", "doc_count": 42}]},
                "risk_scoring": {
                    "buckets": [
                        {"key": "web-server-01", "score": {"value": 150}},
                        {"key": "db-primary", "score": {"value": 85}},
                        {"key": "firewall-hq", "score": {"value": 45}}
                    ]
                },
                "by_time": {
                    "buckets": [
                        {"key_as_string": "2026-02-10T08:00:00Z", "doc_count": 10},
                        {"key_as_string": "2026-02-10T09:00:00Z", "doc_count": 25},
                        {"key_as_string": "2026-02-10T10:00:00Z", "doc_count": 15}
                    ]
                }
            }
        return {"error": str(e)}

def execute_multi_query(queries, index_pattern="wazuh-alerts-*", size_limit=100):
    client = get_client()
    try:
        if index_pattern not in ALLOWED_INDEXES:
            raise ValueError("Index not allowed")
        body = []
        for q in queries:
            if isinstance(q, str):
                q = json.loads(q)
            hdr = {"index": index_pattern}
            body.append(hdr)
            if "size" not in q or not isinstance(q.get("size"), int):
                q["size"] = size_limit
            else:
                q["size"] = min(q["size"], size_limit)
            body.append(q)
        resp = client.msearch(body=body, request_timeout=REQUEST_TIMEOUT)
        out = []
        for r in resp.get("responses", []):
            hits = r.get('hits', {}).get('hits', [])
            total = r.get('hits', {}).get('total', {}).get('value', 0)
            out.append({"total_hits": total, "data": [h.get('_source', {}) for h in hits]})
        return {"status": "success", "results": out}
    except Exception as e:
        logger.error(f"Multi query failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    # Test connection
    client = get_client()
    if client.ping():
        print("Connected to Elasticsearch!")
    else:
        print("Could not connect to Elasticsearch.")
