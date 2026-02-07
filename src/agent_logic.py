from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
import os
import json
import prompts
import elastic_connector

# Memory for context
memory = ConversationBufferMemory(return_messages=True)

def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    return ChatGoogleGenerativeAI(model="gemini-pro", temperature=0, google_api_key=api_key)

def process_query(user_input, schema_context):
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
        # Basic cleanup if LLM adds markdown
        dsl_query_str = dsl_query_str.replace("```json", "").replace("```", "").strip()
        
        results = elastic_connector.execute_query(dsl_query_str)
        
        # 5. Save to memory (optional, depending on what we want to remember)
        memory.save_context({"input": user_input}, {"output": str(results['total_hits'])})
        
        return {
            "query_generated": dsl_query_str,
            "results": results
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Test run
    # Mock schema
    mock_schema = json.dumps({"wazuh-alerts-*": {"event.action": "keyword", "@timestamp": "date"}})
    print(process_query("Show me failed logins", mock_schema))
