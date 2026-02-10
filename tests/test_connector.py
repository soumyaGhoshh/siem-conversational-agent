import os, sys, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

def test_msearch_disallowed_index():
    try:
        elastic_connector = importlib.import_module('elastic_connector')
    except Exception:
        import pytest
        pytest.skip("connector deps not available")
    res = elastic_connector.execute_multi_query([{"query": {}}], index_pattern="bad-index", size_limit=10)
    assert res.get("status") == "error"
