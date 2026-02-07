from elasticsearch import Elasticsearch
import json
import os

# Configuration
ELASTIC_URL = os.getenv("ELASTIC_URL", "https://localhost:9200")
ELASTIC_USER = os.getenv("ELASTIC_USER", "admin")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "SecretPassword1!")
VERIFY_SSL = False

def get_client():
    return Elasticsearch(
        ELASTIC_URL,
        basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
        verify_certs=VERIFY_SSL,
        ssl_show_warn=False
    )

def execute_query(query_dsl, index_pattern="wazuh-alerts-*"):
    """
    Executes a raw DSL query against Elasticsearch.
    """
    client = get_client()
    try:
        # Ensure query is a dict
        if isinstance(query_dsl, str):
            query_dsl = json.loads(query_dsl)
            
        print(f"Executing Query on {index_pattern}...")
        response = client.search(index=index_pattern, body=query_dsl)
        
        hits = response.get('hits', {}).get('hits', [])
        total = response.get('hits', {}).get('total', {}).get('value', 0)
        
        return {
            "status": "success",
            "total_hits": total,
            "data": [hit['_source'] for hit in hits]
        }
        
    except Exception as e:
        print(f"Query Execution Failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    # Test connection
    client = get_client()
    if client.ping():
        print("Connected to Elasticsearch!")
    else:
        print("Could not connect to Elasticsearch.")
