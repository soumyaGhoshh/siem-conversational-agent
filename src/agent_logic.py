from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
import os
import json
import prompts
import elastic_connector
import logging
import validator
import audit
import time

# Memory for context
memory = ConversationBufferMemory(return_messages=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    return ChatGoogleGenerativeAI(model="gemini-pro", temperature=0, google_api_key=api_key)

def process_query(user_input, schema_context, size_limit=100, index_pattern="wazuh-alerts-*", user_name="session", max_lookback_days=None):
    """
    Main entry point for processing user queries.
    """
    # 1. Retrieve history
    history = memory.load_memory_variables({})
    
    # 2. Construct Prompt
    system_msg = prompts.get_system_prompt(schema_context, user_input)
    
    messages = [SystemMessage(content=system_msg)]
    
    # 3. Call LLM
    try:
        llm = get_llm()
        response = llm(messages)
        dsl_query_str = response.content
        
        # 4. Validate & Execute
        dsl_query_str = dsl_query_str.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(dsl_query_str)
        except Exception:
            start = dsl_query_str.find("{")
            end = dsl_query_str.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = dsl_query_str[start:end+1]
                parsed = json.loads(candidate)
            else:
                raise ValueError("LLM did not return valid JSON.")

        try:
            schema_obj = json.loads(schema_context) if isinstance(schema_context, str) else schema_context
        except Exception:
            schema_obj = {}
        fields = validator.flatten_schema(schema_obj)
        types_map = validator.field_types(schema_obj)
        max_days_val = int(os.getenv("MAX_LOOKBACK_DAYS", "7")) if max_lookback_days is None else int(max_lookback_days)
        ok, errs = validator.validate_dsl(parsed, fields, types_map=types_map, max_days=max_days_val)
        if not ok:
            raise ValueError("; ".join(errs))

        start_time = time.perf_counter()
        results = elastic_connector.execute_query(json.dumps(parsed), index_pattern=index_pattern, size_limit=size_limit)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        try:
            audit.init_db()
            audit.log_query(user_name, index_pattern, results.get("total_hits", 0), duration_ms, json.dumps(parsed))
        except Exception:
            pass
        
        # 5. Save to memory (optional, depending on what we want to remember)
        memory.save_context({"input": user_input}, {"output": str(results['total_hits'])})
        
        return {
            "query_generated": dsl_query_str,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Test run
    # Mock schema
    mock_schema = json.dumps({"wazuh-alerts-*": {"event.action": "keyword", "@timestamp": "date"}})
    print(process_query("Show me failed logins", mock_schema))
