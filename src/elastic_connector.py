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
        return False

def execute_query(query_dsl, index_pattern="wazuh-alerts-*", size_limit=100):
    """
    Executes a raw DSL query against Elasticsearch.
    """
    client = get_client()
    try:
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
        return {
            "status": "error",
            "error": str(e)
        }

def execute_aggregation(aggs_dsl, index_pattern="wazuh-alerts-*"):
    client = get_client()
    try:
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
        return {"error": str(e)}

if __name__ == "__main__":
    # Test connection
    client = get_client()
    if client.ping():
        print("Connected to Elasticsearch!")
    else:
        print("Could not connect to Elasticsearch.")
