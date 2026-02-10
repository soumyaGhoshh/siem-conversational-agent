import os
import importlib

def test_index_allowlist_blocks():
    os.environ["ALLOWED_INDEXES"] = "allowed-*"
try:
    import elastic_connector
    importlib.reload(elastic_connector)
except Exception:
    import pytest
    pytest.skip("connector deps not available")
res = elastic_connector.execute_query("{}", index_pattern="blocked-*", size_limit=10)
    assert res.get("status") == "error"
