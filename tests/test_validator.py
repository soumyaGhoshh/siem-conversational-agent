import os
import json
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import validator

schema = {"wazuh-alerts-*": {"@timestamp": "date", "event.action": "keyword", "user.name": "keyword", "destination.port": "integer", "file.path": "keyword"}}
fields = validator.flatten_schema(schema)
types = validator.field_types(schema)

def test_wildcard_only_on_text_keyword():
    dsl = {"query": {"bool": {"must": [{"wildcard": {"destination.port": "*22*"}}, {"range": {"@timestamp": {"gte": "now-1h"}}}]}}}
    ok, errs = validator.validate_dsl(dsl, fields, types_map=types, max_days=7)
    assert not ok and any("Wildcard" in e for e in errs)

def test_date_range_only_on_timestamp():
    dsl = {"query": {"bool": {"must": [{"range": {"event.action": {"gte": "now-1h"}}}, {"range": {"@timestamp": {"gte": "now-1h"}}}]}}}
    ok, errs = validator.validate_dsl(dsl, fields, types_map=types, max_days=7)
    assert not ok and any("Date range only allowed" in e for e in errs)

def test_size_cap():
    dsl = {"size": 2000, "query": {"bool": {"must": [{"term": {"event.action": "x"}}, {"range": {"@timestamp": {"gte": "now-1h"}}}]}}}
    ok, errs = validator.validate_dsl(dsl, fields, types_map=types, max_days=7)
    assert not ok and any("Invalid size" in e for e in errs)

def test_lookback_cap():
    dsl = {"size": 10, "query": {"bool": {"must": [{"term": {"event.action": "x"}}, {"range": {"@timestamp": {"gte": "now-10d"}}}]}}}
    ok, errs = validator.validate_dsl(dsl, fields, types_map=types, max_days=7)
    assert not ok and any("Lookback" in e for e in errs)

def test_match_not_on_keyword_when_analyzed():
    schema2 = {"wazuh-alerts-*": {"event.action": "keyword", "@timestamp": "date"}}
    fields2 = validator.flatten_schema(schema2)
    types2 = validator.field_types(schema2)
    analyzers = {"wazuh-alerts-*": {"event.action": ""}}
    dsl = {"query": {"bool": {"must": [{"match": {"event.action": "x"}}, {"range": {"@timestamp": {"gte": "now-1h"}}}]}}}
    ok, errs = validator.validate_dsl(dsl, fields2, types_map=types2, max_days=7, analyzers_map=analyzers.get("wazuh-alerts-*"))
    assert not ok and any("keyword" in e for e in errs)

def test_nested_field_requires_nested():
    schema3 = {"wazuh-alerts-*": {"user": "nested", "@timestamp": "date"}}
    fields3 = validator.flatten_schema(schema3)
    types3 = validator.field_types(schema3)
    dsl = {"query": {"bool": {"must": [{"range": {"user": {"gte": 1}}}, {"range": {"@timestamp": {"gte": "now-1h"}}}]}}}
    ok, errs = validator.validate_dsl(dsl, fields3, types_map=types3, max_days=7)
    assert not ok and any("Nested" in e for e in errs)
