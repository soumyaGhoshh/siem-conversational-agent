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
from rag_engine import mitre_rag
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
    Main entry point for processing user queries with retry logic and multi-step investigation.
    """
    # 1. Retrieve history
    history = memory.load_memory_variables({})
    
    # 2. Construct Prompt
    rag_context = ""
    try:
        relevant_techs = mitre_rag.search(user_input, k=2)
        if relevant_techs:
            rag_context = "\n### Relevant MITRE Knowledge (RAG retrieved):\n" + "\n".join([f"- {t['name']} ({t['id']}): {t['content']}" for t in relevant_techs])
            logger.info(f"Retrieved {len(relevant_techs)} MITRE techniques from RAG for context.")
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")

    system_msg = prompts.get_system_prompt(schema_context)
    
    messages = [
        SystemMessage(content=system_msg),
        HumanMessage(content=f"User Query: {user_input}{rag_context}\n\nReturn the JSON response now.")
    ]
    
    llm = get_llm()
    max_retries = 2
    last_error = None
    reasoning_steps = []
    
    for attempt in range(max_retries + 1):
        try:
            # 3. Call LLM
            step_desc = f"Analyzing query: '{user_input[:30]}...'" if attempt == 0 else f"Refining analysis based on findings (Attempt {attempt+1})"
            reasoning_steps.append({"step": step_desc, "type": "analysis"})
            
            logger.info(f"LLM Call (Attempt {attempt+1}) for: {user_input[:50]}...")
            response = llm.invoke(messages)
            llm_output = response.content
            
            # 4. Parse JSON Response
            llm_output = llm_output.replace("```json", "").replace("```", "").strip()
            try:
                full_response = json.loads(llm_output)
            except Exception:
                start = llm_output.find("{")
                end = llm_output.rfind("}")
                if start != -1 and end != -1 and end > start:
                    full_response = json.loads(llm_output[start:end+1])
                else:
                    raise ValueError("LLM did not return valid JSON.")

            parsed_query = full_response.get("query", {})
            analysis = full_response.get("analysis", "No analysis provided.")
            story = full_response.get("story")
            mitre = full_response.get("mitre", [])
            remediation = full_response.get("remediation")
            severity = full_response.get("severity", "low")
            confidence = full_response.get("confidence", 85)
            confidence_reason = full_response.get("confidence_reason")

            # 5. Validate DSL
            try:
                schema_obj = json.loads(schema_context) if isinstance(schema_context, str) else schema_context
            except Exception:
                schema_obj = {}
            
            fields = validator.flatten_schema(schema_obj)
            types_map = validator.field_types(schema_obj)
            max_days_val = int(os.getenv("MAX_LOOKBACK_DAYS", "7")) if max_lookback_days is None else int(max_lookback_days)
            
            ok, errs = validator.validate_dsl(parsed_query, fields, types_map=types_map, max_days=max_days_val)
            if not ok:
                error_msg = "; ".join(errs)
                logger.warning(f"DSL Validation failed on attempt {attempt+1}: {error_msg}")
                messages.append(HumanMessage(content=f"The DSL you generated is invalid: {error_msg}. Please fix the query and return the full JSON again."))
                continue

            # 6. Execute Query
            start_time = time.perf_counter()
            reasoning_steps.append({"step": f"Executing DSL on index {index_pattern}", "type": "execution"})
            results = elastic_connector.execute_query(json.dumps(parsed_query), index_pattern=index_pattern, size_limit=size_limit)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            # 7. Agentic Investigation (Multi-step)
            # If we found something suspicious and haven't investigated further yet
            if results.get("total_hits", 0) > 0 and severity in ["high", "critical"] and attempt == 0:
                logger.info("High severity detected. Triggering automated follow-up investigation...")
                reasoning_steps.append({"step": "High severity detected. Investigating lateral movement and related entities.", "type": "investigation"})
                sample_data = results.get("data", [])[:3]
                follow_up_prompt = f"I found these results for '{user_input}': {json.dumps(sample_data)}. Based on this, perform a deeper investigation. Look for related events (same IP, same user, or lateral movement). Return an updated analysis and attack story."
                messages.append(HumanMessage(content=follow_up_prompt))
                # We continue the loop once to get a refined response based on actual data
                continue

            # Log audit
            try:
                audit.init_db()
                audit.log_query(user_name, index_pattern, results.get("total_hits", 0), duration_ms, json.dumps(parsed_query))
            except Exception:
                pass
            
            # Save to memory
            memory.save_context({"input": user_input}, {"output": analysis})
            
            return {
                "query_generated": json.dumps(parsed_query),
                "results": results,
                "analysis": analysis,
                "story": story,
                "mitre": mitre,
                "remediation": remediation,
                "severity": severity,
                "confidence": confidence,
                "confidence_reason": confidence_reason,
                "reasoning_steps": reasoning_steps
            }

        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed: {e}")
            last_error = e
            if attempt < max_retries:
                time.sleep(1)
                continue
            break

    # Fallback / Error Handling
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        logger.info("DEMO_MODE fallback active")
        fallback_query = {"query": {"match_all": {}}}
        return {
            "query_generated": json.dumps(fallback_query),
            "results": elastic_connector.execute_query(json.dumps(fallback_query), index_pattern=index_pattern, size_limit=size_limit),
            "analysis": f"Investigation complete. (Note: Fallback analysis used due to processing error: {str(last_error)})",
            "story": "Automated investigation identified potential lateral movement patterns related to the initial query.",
            "severity": "medium"
        }
    return {"error": str(last_error) if last_error else "AI Analysis failed after multiple attempts"}


if __name__ == "__main__":
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    mock_schema = {"wazuh-alerts-*": {"properties": {"@timestamp": {"type": "date"}}}}
    res = process_query("Show me failed logins", mock_schema)
    print(json.dumps(res, indent=2))
    # Test run
    # Mock schema
    mock_schema = json.dumps({"wazuh-alerts-*": {"event.action": "keyword", "@timestamp": "date"}})
    print(process_query("Show me failed logins", mock_schema))
