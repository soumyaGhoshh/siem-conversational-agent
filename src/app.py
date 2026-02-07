import streamlit as st
import agent_logic
import schema_extractor
import os
import time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI SIEM Analyst", layout="wide")

st.title("🛡️ AI Security Analyst Interface")
st.markdown("ask questions about your Wazuh/Elastic logs in natural language.")

# Sidebar for configuration
with st.sidebar:
    st.header("System Status")
    if st.button("Refresh Schema"):
        with st.spinner("Fetching schema..."):
            mapping = schema_extractor.get_index_mapping("wazuh-alerts-*")
            if mapping:
                schema = schema_extractor.simplify_mapping(mapping)
                st.session_state['schema'] = schema
                st.success("Schema updated!")
            else:
                st.error("Could not fetch schema. Ensure Wazuh is running.")

    if 'schema' in st.session_state:
        st.json(st.session_state['schema'], expanded=False)
    else:
        st.warning("No schema loaded.")

# Main Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "results" in message:
            with st.expander("View Query Results"):
                st.json(message["results"])

# User Input
if prompt := st.chat_input("Show me failed logins from the last 24 hours"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            # Get schema context
            schema_context = st.session_state.get('schema', {})
            
            # Process query
            response = agent_logic.process_query(prompt, str(schema_context))
            
            if "error" in response:
                st.error(f"Error: {response['error']}")
                result_content = f"I encountered an error: {response['error']}"
            else:
                generated_query = response.get("query_generated", "No query generated")
                st.markdown(f"**Generated Query:**\n```json\n{generated_query}\n```")
                
                results = response.get("results", {})
                hits = results.get("total_hits", 0)
                st.markdown(f"Found **{hits}** matching events.")
                
                if hits > 0:
                    st.dataframe(results.get("data", []))
                
                result_content = f"Executed query. Found {hits} hits."
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": result_content,
                "results": response
            })
