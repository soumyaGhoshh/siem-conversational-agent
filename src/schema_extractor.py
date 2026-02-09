import requests
import json
import os
import logging

# Configuration
ELASTIC_URL = os.getenv("ELASTIC_URL", "https://localhost:9200")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"
REQUEST_TIMEOUT = int(os.getenv("ELASTIC_REQUEST_TIMEOUT", "20"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_index_mapping(index_pattern):
    """
    Fetches the mapping for a specific index or pattern.
    """
    url = f"{ELASTIC_URL}/{index_pattern}/_mapping"
    try:
        if not ELASTIC_USER or not ELASTIC_PASSWORD:
            raise ValueError("ELASTIC_USER/ELASTIC_PASSWORD environment variables are not set.")
        response = requests.get(
            url,
            auth=(ELASTIC_USER, ELASTIC_PASSWORD),
            verify=VERIFY_SSL,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching mapping for {index_pattern}: {e}")
        return None
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return None

def simplify_mapping(mapping_data):
    """
    Extracts relevant fields and types from the raw mapping.
    This is a heuristic to reduce token usage.
    """
    if not mapping_data:
        return {}
    
    simplified = {}
    
    # Iterate over indices
    for index_name, details in mapping_data.items():
        mappings = details.get("mappings", {})
        properties = mappings.get("properties", {})
        
        # Flatten properties (basic implementation, might need recursion for nested objects)
        # For this prototype, we'll list top-level and common nested fields found in SIEM events
        # like agent.id, event.action, etc.
        
        flat_props = {}
        
        def recurse_props(props, parent_key=""):
            for key, value in props.items():
                full_key = f"{parent_key}.{key}" if parent_key else key
                if "properties" in value:
                    recurse_props(value["properties"], full_key)
                else:
                    flat_props[full_key] = value.get("type", "keyword")
        
        recurse_props(properties)
        simplified[index_name] = flat_props
        
    return simplified

def save_schema(schema, filename="schema.json"):
    with open(filename, "w") as f:
        json.dump(schema, f, indent=2)
    logger.info(f"Schema saved to {filename}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("Fetching wazuh-alerts-* mapping...")
    mapping = get_index_mapping("wazuh-alerts-*")
    
    if mapping:
        simple_schema = simplify_mapping(mapping)
        save_schema(simple_schema, "wazuh_schema.json")
    else:
        logger.error("Failed to retrieve mapping.")
