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
from dotenv import load_dotenv

# Memory for context
memory = ConversationBufferMemory(return_messages=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    
    # Try multiple model names in case of availability issues
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro", "gemini-2.0-flash", "gemini-2.0-flash-exp"]
    
    last_err = None
    for model_name in models_to_try:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name, 
                temperature=0, 
                google_api_key=api_key,
                max_retries=1
            )
            # Test it with a very simple call if possible, or just return it
            return llm
        except Exception as e:
            logger.warning(f"Failed to initialize model {model_name}: {e}")
            last_err = e
            continue
            
    raise last_err or ValueError("Could not initialize any Gemini model.")

def process_query(user_input, schema_context, size_limit=100, index_pattern="wazuh-alerts-*", user_name="session", max_lookback_days=None):
    """
    Main entry point for processing user queries.
    """
    # 1. Retrieve history
    history = memory.load_memory_variables({})
    
    # 2. Construct Prompt
    system_msg = prompts.get_system_prompt(schema_context)
    
    messages = [
        SystemMessage(content=system_msg),
        HumanMessage(content=f"User Query: {user_input}\n\nReturn the JSON response now.")
    ]
    
    # 3. Call LLM
    try:
        logger.info(f"Calling LLM with user input: {user_input}")
        llm = get_llm()
        response = llm.invoke(messages)
        llm_output = response.content
        logger.info(f"LLM Output: {llm_output}")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        if os.getenv("DEMO_MODE", "false").lower() == "true":
            logger.info("DEMO_MODE active: Using fallback LLM response")
            # Simple heuristic for fallback analysis based on input
            fallback_query = {"query": {"match_all": {}}}
            if "fail" in user_input.lower() or "login" in user_input.lower():
                fallback_query = {"query": {"bool": {"must": [{"match": {"event.action": "logon-failure"}}]}}}
            
            return {
                "query_generated": json.dumps(fallback_query),
                "results": elastic_connector.execute_query(json.dumps(fallback_query), index_pattern=index_pattern, size_limit=size_limit),
                "analysis": "LLM is currently unavailable (Quota Limit). This is a fallback analysis identifying potential authentication failures in the environment.",
                "story": "Demo Mode: Multiple failed login attempts detected across distributed endpoints, suggesting a possible credential stuffing attempt.",
                "severity": "medium"
            }
        return {"error": f"AI Analysis failed: {str(e)}"}

    # 4. Parse JSON Response
    try:
        llm_output = llm_output.replace("```json", "").replace("```", "").strip()
        try:
            full_response = json.loads(llm_output)
        except Exception as e:
            logger.warning(f"Initial JSON parse failed: {e}. Trying fallback.")
            # Fallback for messy LLM output
            start = llm_output.find("{")
            end = llm_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = llm_output[start:end+1]
                full_response = json.loads(candidate)
            else:
                logger.error(f"LLM output was not JSON: {llm_output}")
                raise ValueError("LLM did not return valid JSON.")

        parsed_query = full_response.get("query", {})
        analysis = full_response.get("analysis", "No analysis provided.")
        story = full_response.get("story")
        remediation = full_response.get("remediation")
        severity = full_response.get("severity", "low")
        
        logger.info(f"Parsed LLM response: query_keys={list(parsed_query.keys()) if parsed_query else 'None'}, severity={severity}")

        # 5. Validate & Execute Query
        try:
            schema_obj = json.loads(schema_context) if isinstance(schema_context, str) else schema_context
        except Exception:
            schema_obj = {}
        
        fields = validator.flatten_schema(schema_obj)
        types_map = validator.field_types(schema_obj)
        max_days_val = int(os.getenv("MAX_LOOKBACK_DAYS", "7")) if max_lookback_days is None else int(max_lookback_days)
        
        ok, errs = validator.validate_dsl(parsed_query, fields, types_map=types_map, max_days=max_days_val)
        if not ok:
            raise ValueError("; ".join(errs))

        start_time = time.perf_counter()
        results = elastic_connector.execute_query(json.dumps(parsed_query), index_pattern=index_pattern, size_limit=size_limit)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        try:
            audit.init_db()
            audit.log_query(user_name, index_pattern, results.get("total_hits", 0), duration_ms, json.dumps(parsed_query))
        except Exception:
            pass
        
        # 6. Save to memory
        memory.save_context({"input": user_input}, {"output": analysis})
        
        return {
            "query_generated": json.dumps(parsed_query),
            "results": results,
            "analysis": analysis,
            "story": story,
            "remediation": remediation,
            "severity": severity
        }
    except Exception as e:
        logger.error(f"Processing error: {e}")
        if os.getenv("DEMO_MODE", "false").lower() == "true":
            return {
                "query_generated": json.dumps({"query": {"match_all": {}}}),
                "results": elastic_connector.execute_query(json.dumps({"query": {"match_all": {}}}), index_pattern=index_pattern, size_limit=size_limit),
                "analysis": f"Processing error: {str(e)}. Using fallback.",
                "story": None,
                "severity": "low"
            }
        return {"error": str(e)}

if __name__ == "__main__":
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    mock_schema = {"wazuh-alerts-*": {"properties": {"@timestamp": {"type": "date"}}}}
    res = process_query("Show me failed logins", mock_schema)
    print(json.dumps(res, indent=2))
    # Test run
    # Mock schema
    mock_schema = json.dumps({"wazuh-alerts-*": {"event.action": "keyword", "@timestamp": "date"}})
    print(process_query("Show me failed logins", mock_schema))
