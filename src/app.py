import streamlit as st
import agent_logic
import schema_extractor
import elastic_connector
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI SIEM Analyst", layout="wide")
st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(180deg, #0b1220 0%, #0e1a2b 100%);} 
    .stSidebar {background-color: #0e1a2b;}
    h1, h2, h3, h4 {color: #e6edf3;}
    .stMarkdown, .stText {color: #c9d1d9;}
    .stChatMessage .stMarkdown {color: #c9d1d9;}
    div[data-baseweb="toast"] {background-color: #0b1220; color: #c9d1d9;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛡️ AI Security Analyst Interface")
st.markdown("Ask questions about your Wazuh/OpenSearch logs in natural language.")

# Sidebar for configuration
with st.sidebar:
    st.header("System Status")
    if "authed" not in st.session_state:
        st.session_state["authed"] = False
    token_input = st.text_input("Access token", type="password")
    user_name = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        expected = os.getenv("ADMIN_TOKEN", "")
        if token_input and expected and token_input == expected:
            try:
                import user_store
                ok, role = user_store.verify_user(user_name.strip(), password.strip())
                if ok:
                    st.session_state["authed"] = True
                    st.session_state["user_name"] = user_name.strip() or "user"
                    st.session_state["role"] = role
                    st.success("Authenticated")
                else:
                    st.error("Invalid username or password")
            except Exception as e:
                st.error(str(e))
        else:
            st.error("Invalid token")
    if not st.session_state["authed"]:
        st.stop()
    cols = st.columns(2)
    with cols[0]:
        if st.button("Refresh Schema"):
            with st.spinner("Fetching schema..."):
                mapping = schema_extractor.get_index_mapping("wazuh-alerts-*")
                if mapping:
                    schema = schema_extractor.simplify_mapping(mapping)
                    st.session_state['schema'] = schema
                    st.success("Schema updated")
                else:
                    st.error("Schema fetch failed")
    with cols[1]:
        if st.button("Test Connection"):
            ok = elastic_connector.ping()
            if ok:
                st.success("Elasticsearch reachable")
            else:
                st.error("Elasticsearch not reachable")

    # Preflight panel
    st.subheader("Preflight")
    es_ok = elastic_connector.ping()
    creds_ok = bool(os.getenv("ELASTIC_USER")) and bool(os.getenv("ELASTIC_PASSWORD"))
    api_ok = bool(os.getenv("GOOGLE_API_KEY"))
    schema_ok = 'schema' in st.session_state
    st.write({"Elasticsearch": es_ok, "Creds": creds_ok, "LLM Key": api_ok, "Schema": schema_ok})

    role_cur = st.session_state.get("role", "analyst")
    allowed_env = os.getenv("ALLOWED_INDEXES_ANALYST" if role_cur == "analyst" else "ALLOWED_INDEXES_ADMIN", os.getenv("ALLOWED_INDEXES", "wazuh-alerts-*"))
    allowed_list = [s.strip() for s in allowed_env.split(",") if s.strip()]
    index_pattern = st.selectbox("Index pattern", allowed_list, index=0)
    st.session_state['index_pattern'] = index_pattern

    size_limit = st.slider("Max results", 10, 500, st.session_state.get('size_limit', 100), 10)
    st.session_state['size_limit'] = size_limit
    page_size = st.slider("Rows per page", 10, 100, st.session_state.get('page_size', 20), 10)
    st.session_state['page_size'] = page_size

    time_range = st.radio("Time range", ["Unspecified", "Last 1 hour", "Last 24 hours", "Last 7 days"], index=1)
    st.session_state['time_range'] = time_range

    if st.button("Clear Chat"):
        st.session_state['messages'] = []

    st.subheader("Quick Queries")
    if st.button("Failed logins (24h)"):
        st.session_state['pending_prompt'] = "Show me failed logins from the last 24 hours"
    if st.button("RDP connections (24h)"):
        st.session_state['pending_prompt'] = "Show me RDP connections in the last 24 hours"
    if st.button("Suspicious file access"):
        st.session_state['pending_prompt'] = "List all users who accessed /etc/shadow"

    if 'schema' in st.session_state:
        st.json(st.session_state['schema'], expanded=False)
    else:
        st.warning("No schema loaded")

    st.subheader("Sigma Mini Gallery")
    if st.button("Sigma: Failed logins 24h"):
        idx = st.session_state.get('index_pattern', 'wazuh-alerts-*')
        dsl = {"size": 100, "query": {"bool": {"must": [{"match": {"event.action": "logon-failure"}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}}
        res = elastic_connector.execute_query(json.dumps(dsl), index_pattern=idx, size_limit=100)
        st.session_state['builder_result'] = {"query_generated": json.dumps(dsl), "results": res}
        st.success("Sigma rule executed")
    if st.button("Sigma: RDP 24h"):
        idx = st.session_state.get('index_pattern', 'wazuh-alerts-*')
        dsl = {"size": 100, "query": {"bool": {"must": [{"term": {"destination.port": 3389}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}}
        res = elastic_connector.execute_query(json.dumps(dsl), index_pattern=idx, size_limit=100)
        st.session_state['builder_result'] = {"query_generated": json.dumps(dsl), "results": res}
        st.success("Sigma rule executed")
    if st.button("Sigma: /etc/shadow access"):
        idx = st.session_state.get('index_pattern', 'wazuh-alerts-*')
        dsl = {"size": 100, "query": {"bool": {"must": [{"term": {"file.path": "/etc/shadow"}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}}
        res = elastic_connector.execute_query(json.dumps(dsl), index_pattern=idx, size_limit=100)
        st.session_state['builder_result'] = {"query_generated": json.dumps(dsl), "results": res}
        st.success("Sigma rule executed")

    # Deterministic Query Builder
    st.subheader("Query Builder")
    schema_obj = st.session_state.get('schema', {})
    schema_fields_list = list(next(iter(schema_obj.values())).keys()) if schema_obj else []
    qb_field = st.selectbox("Field", schema_fields_list)
    qb_val = st.text_input("Value")
    types_map = None
    try:
        from validator import field_types
        types_map = field_types(schema_obj)
    except Exception:
        types_map = {}
    ftype = types_map.get(qb_field, "keyword")
    allowed_ops = ["term", "match", "wildcard"] if ftype in ("keyword", "text") else ["term", "range"]
    qb_op = st.selectbox("Operator", allowed_ops)
    try:
        analyzers = schema_extractor.field_analyzers(schema_extractor.get_index_mapping(st.session_state.get('index_pattern', 'wazuh-alerts-*')))
        am = analyzers.get(st.session_state.get('index_pattern', 'wazuh-alerts-*'), {})
        an = am.get(qb_field, "")
        st.caption(f"Analyzer: {an or 'n/a'} | Allowed ops: {', '.join(allowed_ops)}")
        if an and qb_op == "wildcard":
            st.warning("Wildcard not allowed on analyzed text fields")
    except Exception:
        pass
    qb_tr = st.selectbox("Time range", ["Last 1 hour", "Last 24 hours", "Last 7 days"], index=1)
    qb_size = st.number_input("Size", min_value=1, max_value=500, value=100)
    if st.button("Run Builder"):
        idx = st.session_state.get('index_pattern', 'wazuh-alerts-*')
        tr_map = {"Last 1 hour": "now-1h", "Last 24 hours": "now-24h", "Last 7 days": "now-7d"}
        gte = tr_map.get(qb_tr, "now-24h")
        dsl = {
            "size": qb_size,
            "query": {
                "bool": {
                    "must": [
                        {qb_op: {qb_field: qb_val}},
                        {"range": {"@timestamp": {"gte": gte}}}
                    ]
                }
            }
        }
        try:
            from validator import flatten_schema, field_types, validate_dsl
            schema_obj = st.session_state.get('schema', {})
            fields = flatten_schema(schema_obj)
            types_map = field_types(schema_obj)
            max_days = 7 if st.session_state.get("role", "analyst") == "analyst" else int(os.getenv("MAX_LOOKBACK_DAYS", "30"))
            analyzers = schema_extractor.field_analyzers(schema_extractor.get_index_mapping(idx))
            am = analyzers.get(idx, {})
            ok, errs = validate_dsl(dsl, fields, types_map=types_map, max_days=max_days, analyzers_map=am)
            if not ok:
                if "Nested field requires nested query context" in "; ".join(errs):
                    st.code(json.dumps({"query": {"nested": {"path": qb_field.split(".")[0], "query": {qb_op: {qb_field: qb_val}}}}}, indent=2))
                st.error("; ".join(errs))
            else:
                res = elastic_connector.execute_query(json.dumps(dsl), index_pattern=idx, size_limit=qb_size)
                st.session_state['builder_result'] = {"query_generated": json.dumps(dsl), "results": res}
                st.success("Builder query executed")
        except Exception as e:
            st.error(str(e))

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
prompt = None
user_typed = st.chat_input("Ask about Wazuh/OpenSearch events")
if user_typed:
    prompt = user_typed
elif 'pending_prompt' in st.session_state:
    prompt = st.session_state.pop('pending_prompt')
if prompt:
    tr = st.session_state.get('time_range', 'Unspecified')
    if tr != 'Unspecified' and 'last' not in prompt.lower():
        prompt = f"{prompt} ({tr.lower()})"
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            # Get schema context
            schema_context = st.session_state.get('schema', {})
            
            # Process query
            qc = st.session_state.get('query_times', [])
            now = time.time()
            window = 60
            max_q = int(os.getenv("MAX_QUERIES_PER_MIN", "10"))
            qc = [t for t in qc if now - t < window]
            if len(qc) >= max_q:
                st.error("Rate limit exceeded")
                response = {"error": "Rate limit"}
            else:
                qc.append(now)
                st.session_state['query_times'] = qc
                max_days = 7 if st.session_state.get("role", "analyst") == "analyst" else int(os.getenv("MAX_LOOKBACK_DAYS", "30"))
                response = agent_logic.process_query(prompt, str(schema_context), size_limit=st.session_state.get('size_limit', 100), index_pattern=st.session_state.get('index_pattern', 'wazuh-alerts-*'), user_name=st.session_state.get('user_name', 'user'), max_lookback_days=max_days)
            
            if "error" in response:
                st.error(f"Error: {response['error']}")
                result_content = f"I encountered an error: {response['error']}"
            else:
                generated_query = response.get("query_generated", "No query generated")
                results = response.get("results", {})
                hits = results.get("total_hits", 0)

                tabs = st.tabs(["Overview", "Results", "Query DSL", "Audit", "Saved Searches", "Alerts"])
                with tabs[0]:
                    st.markdown(f"Found **{hits}** matching events.")
                    data = results.get("data", [])
                    # ES aggregations for top-N and timeline
                    idx = st.session_state.get('index_pattern', 'wazuh-alerts-*')
                    if 'schema' in st.session_state and st.session_state['schema']:
                        schema_fields = list(next(iter(st.session_state['schema'].values())).keys())
                    else:
                        schema_fields = []
                    agg_field = st.selectbox("Summarize by field", schema_fields or (data[0].keys() if data else []))
                    if agg_field:
                        terms_dsl = {
                            "size": 0,
                            "aggs": {"top_terms": {"terms": {"field": agg_field, "size": 10}}}
                        }
                        try:
                            import altair as alt
                            aggs = elastic_connector.execute_aggregation(json.dumps(terms_dsl), index_pattern=idx)
                            buckets = aggs.get('top_terms', {}).get('buckets', []) if isinstance(aggs, dict) else []
                            data_terms = [{"value": b.get('key'), "count": b.get('doc_count', 0)} for b in buckets]
                            chart_terms = alt.Chart(alt.Data(values=data_terms)).mark_bar().encode(
                                x=alt.X("value:N", title="Value"),
                                y=alt.Y("count:Q", title="Count"),
                                tooltip=["value", "count"]
                            )
                            st.altair_chart(chart_terms, use_container_width=True)
                            sel_val = st.selectbox("Filter value", [d["value"] for d in data_terms] if data_terms else [])
                            if sel_val and st.button("Run filter"):
                                fdsl = {"size": 100, "query": {"bool": {"must": [{"term": {agg_field: sel_val}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}}
                                fres = elastic_connector.execute_query(json.dumps(fdsl), index_pattern=idx, size_limit=100)
                                st.json(fres)
                        except Exception:
                            pass
                    # Timeline
                    histo_dsl = {
                        "size": 0,
                        "aggs": {"by_time": {"date_histogram": {"field": "@timestamp", "fixed_interval": "1h"}}}
                    }
                    try:
                        import altair as alt
                        haggs = elastic_connector.execute_aggregation(json.dumps(histo_dsl), index_pattern=idx)
                        hb = haggs.get('by_time', {}).get('buckets', []) if isinstance(haggs, dict) else []
                        data_chart = [{"bucket": i, "count": b.get('doc_count', 0)} for i, b in enumerate(hb)]
                        chart = alt.Chart(alt.Data(values=data_chart)).mark_line(point=True).encode(
                            x=alt.X("bucket:Q", title="Hour bucket"),
                            y=alt.Y("count:Q", title="Events"),
                            tooltip=["bucket", "count"]
                        )
                        st.altair_chart(chart, use_container_width=True)
                        sel_bucket = st.selectbox("Filter bucket", list(range(len(data_chart))))
                        if st.button("Run bucket filter") and hb:
                            key = hb[sel_bucket].get('key_as_string') or hb[sel_bucket].get('key')
                            fdsl = {"size": 100, "query": {"bool": {"must": [{"range": {"@timestamp": {"gte": key, "lt": f"{key}||+1h"}}}]}}}
                            fres = elastic_connector.execute_query(json.dumps(fdsl), index_pattern=idx, size_limit=100)
                            st.json(fres)
                    except Exception:
                        pass

                        # Correlation and risk scoring
                        if st.button("Run correlation (24h)"):
                            idx = st.session_state.get('index_pattern', 'wazuh-alerts-*')
                            q_failed = {
                                "size": 200,
                                "query": {"bool": {"must": [{"match": {"event.action": "logon-failure"}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}
                            }
                            q_rdp = {
                                "size": 200,
                                "query": {"bool": {"must": [{"term": {"destination.port": 3389}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}
                            }
                            q_file = {
                                "size": 200,
                                "query": {"bool": {"must": [{"term": {"file.path": "/etc/shadow"}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}
                            }
                            rf = elastic_connector.execute_query(json.dumps(q_failed), index_pattern=idx, size_limit=200)
                            rr = elastic_connector.execute_query(json.dumps(q_rdp), index_pattern=idx, size_limit=200)
                            rfile = elastic_connector.execute_query(json.dumps(q_file), index_pattern=idx, size_limit=200)
                            score = {}
                            def bump(key, w):
                                score[key] = score.get(key, 0) + w
                            for h in rf.get("data", []):
                                u = h.get("user", h.get("user.name", "unknown"))
                                bump(u, 2)
                            for h in rr.get("data", []):
                                u = h.get("user", h.get("user.name", "unknown"))
                                bump(u, 1)
                            for h in rfile.get("data", []):
                                u = h.get("user", h.get("user.name", "unknown"))
                                bump(u, 3)
                            top = sorted(score.items(), key=lambda x: x[1], reverse=True)[:10]
                            st.table({"entity": [k for k, _ in top], "risk": [v for _, v in top]})
                        alert_threshold = st.number_input("Alert threshold", min_value=1, value=100)
                        webhook = os.getenv("WEBHOOK_URL", "")
                        if hits >= alert_threshold and webhook:
                            try:
                                import requests
                                requests.post(webhook, json={"hits": hits, "query": generated_query})
                                st.success("Alert sent")
                            except Exception:
                                st.warning("Could not send alert")

                with tabs[1]:
                    data = results.get("data", [])
                    if data:
                        first = data[0]
                        all_fields = list(first.keys())
                        cols_to_show = st.multiselect("Columns", all_fields, default=all_fields[:min(10, len(all_fields))])
                        total_rows = len(data)
                        page_size = st.session_state.get('page_size', 20)
                        total_pages = max(1, (total_rows + page_size - 1) // page_size)
                        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
                        start = (page - 1) * page_size
                        end = start + page_size
                        sliced = data[start:end]
                        if cols_to_show:
                            sliced = [{k: r.get(k) for k in cols_to_show} for r in sliced]
                        # Optional PII redaction
                        redaction_on = st.checkbox("Redact PII fields", value=bool(os.getenv("REDACT_PII", "false").lower() == "true"))
                        pii_fields = ["user.email", "http.request.body.content", "message"]
                        if redaction_on:
                            rsliced = []
                            for r in sliced:
                                nr = dict(r)
                                for pf in pii_fields:
                                    if pf in nr and isinstance(nr[pf], str):
                                        nr[pf] = "***"
                                rsliced.append(nr)
                            sliced = rsliced
                        st.dataframe(sliced)
                        try:
                            import csv
                            import io
                            output = io.StringIO()
                            if sliced:
                                w = csv.DictWriter(output, fieldnames=list(sliced[0].keys()))
                                w.writeheader()
                                w.writerows(sliced)
                                st.download_button("Download CSV", output.getvalue(), file_name="results.csv", mime="text/csv")
                        except Exception:
                            pass
                    else:
                        st.info("No results to display")

                with tabs[2]:
                    st.markdown(f"```json\n{generated_query}\n```")
                    try:
                        parsed = json.loads(generated_query)
                        size = parsed.get("size", None)
                        q = parsed.get("query", {})
                        ts_present = "range" in str(q)
                        st.markdown(f"Query summary: size={size if size is not None else 'default'}, {'time range present' if ts_present else 'no explicit time range'}")
                        st.download_button("Download DSL", data=generated_query, file_name="query.json", mime="application/json")
                    except Exception:
                        st.warning("Could not parse generated query")

                with tabs[3]:
                    try:
                        import audit
                        audit.init_db()
                        rows = audit.list_queries()
                        st.table({"ts": [r[0] for r in rows], "user": [r[1] for r in rows], "index": [r[2] for r in rows], "hits": [r[3] for r in rows], "duration_ms": [r[4] for r in rows]})
                        if st.button("Export audit with signature"):
                            res = audit.export_queries_json(os.getenv("AUDIT_SIGNING_KEY"))
                            st.json(res)
                        days = st.number_input("Retention days", min_value=1, value=30)
                        if st.button("Prune old audits"):
                            audit.prune_old_queries(int(days))
                            st.success("Pruned")
                    except Exception as e:
                        st.warning(str(e))

                with tabs[4]:
                    try:
                        import audit
                        audit.init_db()
                        name = st.text_input("Saved search name")
                        if st.button("Save current DSL") and generated_query:
                            audit.save_search(name or "search", st.session_state.get('user_name', 'user'), st.session_state.get('index_pattern', 'wazuh-alerts-*'), generated_query)
                            st.success("Saved")
                        rows = audit.list_saved_searches(st.session_state.get('user_name', None))
                        st.table({"id": [r[0] for r in rows], "name": [r[1] for r in rows], "index": [r[2] for r in rows]})
                        sel = st.number_input("Run saved id", min_value=0, value=0)
                        if st.button("Run saved") and sel > 0:
                            row = audit.get_saved_search(int(sel))
                            if row:
                                qjson, idx = row
                                res2 = elastic_connector.execute_query(qjson, index_pattern=idx, size_limit=st.session_state.get('size_limit', 100))
                                st.json(res2)
                    except Exception as e:
                        st.warning(str(e))

                with tabs[5]:
                    try:
                        import audit
                        audit.init_db()
                        aname = st.text_input("Alert name")
                        athr = st.number_input("Hits threshold", min_value=1, value=10)
                        awin = st.selectbox("Time window", ["1h", "24h", "7d"], index=1)
                        if st.button("Add Alert"):
                            audit.add_alert(aname or "alert", st.session_state.get('user_name', 'user'), st.session_state.get('index_pattern', 'wazuh-alerts-*'), athr, awin)
                            st.success("Alert added")
                        rows = audit.list_alerts(st.session_state.get('user_name', None))
                        st.table({"id": [r[0] for r in rows], "name": [r[1] for r in rows], "index": [r[2] for r in rows], "threshold": [r[3] for r in rows], "window": [r[4] for r in rows], "last_trigger": [r[5] for r in rows]})
                        if hits is not None:
                            sel_alert_id = st.number_input("Evaluate alert id", min_value=0, value=0)
                            if st.button("Evaluate Alert") and sel_alert_id > 0:
                                try:
                                    for r in rows:
                                        if r[0] == int(sel_alert_id) and hits >= int(r[3]):
                                            audit.mark_alert_triggered(int(sel_alert_id))
                                            st.success("Alert triggered")
                                except Exception as e:
                                    st.warning(str(e))
                    except Exception as e:
                        st.warning(str(e))

                triage_tab = st.tabs(["Triage", "Sigma Coverage"])[0]
                with triage_tab:
                    idx = st.session_state.get('index_pattern', 'wazuh-alerts-*')
                    q_failed = {"size": 100, "query": {"bool": {"must": [{"match": {"event.action": "logon-failure"}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}}
                    q_rdp = {"size": 100, "query": {"bool": {"must": [{"term": {"destination.port": 3389}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}}
                    q_shadow = {"size": 100, "query": {"bool": {"must": [{"term": {"file.path": "/etc/shadow"}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}}
                    resp = elastic_connector.execute_multi_query([q_failed, q_rdp, q_shadow], index_pattern=idx, size_limit=100)
                    if resp.get("status") == "success":
                        st.caption(f"Last run: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
                        reslist = resp.get("results", [])
                        score = {}
                        def bump(key, w):
                            score[key] = score.get(key, 0) + w
                        for h in reslist[0].get("data", []):
                            u = h.get("user", h.get("user.name", "unknown"))
                            bump(u, 2)
                        for h in reslist[1].get("data", []):
                            u = h.get("user", h.get("user.name", "unknown"))
                            bump(u, 1)
                        for h in reslist[2].get("data", []):
                            u = h.get("user", h.get("user.name", "unknown"))
                            bump(u, 3)
                        top = sorted(score.items(), key=lambda x: x[1], reverse=True)[:10]
                        st.table({"entity": [k for k, _ in top], "risk": [v for _, v in top]})
                        sel_ent = st.selectbox("View entity", [k for k, _ in top] if top else [])
                        if sel_ent:
                            samples = []
                            for r in reslist:
                                for h in r.get("data", [])[:5]:
                                    if h.get("user") == sel_ent or h.get("user.name") == sel_ent:
                                        samples.append(h)
                            st.json({"entity": sel_ent, "samples": samples})
                            hook = os.getenv("WEBHOOK_URL", "")
                            if hook and st.button("Send webhook"):
                                try:
                                    import requests
                                    requests.post(hook, json={"entity": sel_ent, "risk": dict(top).get(sel_ent, 0), "samples": samples})
                                    st.success("Webhook sent")
                                except Exception:
                                    st.warning("Webhook failed")

                sigma_tab = st.tabs(["Triage", "Sigma Coverage"])[1]
                with sigma_tab:
                    idx = st.session_state.get('index_pattern', 'wazuh-alerts-*')
                    rules = [
                        ("Failed logons", {"size": 0, "query": {"bool": {"must": [{"match": {"event.action": "logon-failure"}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}}),
                        ("RDP", {"size": 0, "query": {"bool": {"must": [{"term": {"destination.port": 3389}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}}),
                        ("Shadow access", {"size": 0, "query": {"bool": {"must": [{"term": {"file.path": "/etc/shadow"}}, {"range": {"@timestamp": {"gte": "now-24h"}}}]}}})
                    ]
                    counts = []
                    for name, dsl in rules:
                        r = elastic_connector.execute_query(json.dumps(dsl), index_pattern=idx, size_limit=0)
                        counts.append((name, r.get("total_hits", 0)))
                    cov = int(100 * (len([c for c in counts if c[1] > 0]) / len(rules))) if rules else 0
                    st.metric("Sigma coverage", f"{cov}%")
                    st.table({"rule": [n for n, _ in counts], "hits": [c for _, c in counts]})
                
                result_content = f"Executed query. Found {hits} hits."
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": result_content,
                "results": response
            })
