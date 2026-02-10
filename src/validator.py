import json
import re
from datetime import datetime, timedelta

def flatten_schema(schema):
    fields = set()
    for idx, props in schema.items():
        for f in props.keys():
            fields.add(f)
    return fields

def field_types(schema):
    types = {}
    for idx, props in schema.items():
        for f, t in props.items():
            types[f] = t
    return types

def has_time_range(dsl):
    q = dsl.get("query", {})
    s = json.dumps(q)
    return "range" in s and "@timestamp" in s

def within_max_lookback(dsl, max_days=7):
    try:
        rng = dsl.get("query", {}).get("bool", {}).get("must", [])
        for clause in rng:
            if isinstance(clause, dict) and "range" in clause:
                r = clause["range"].get("@timestamp", {})
                gte = r.get("gte")
                if isinstance(gte, str):
                    m = re.match(r"now-(\d+)([dh])", gte)
                    if m:
                        val = int(m.group(1))
                        unit = m.group(2)
                        days = val if unit == 'd' else val/24
                        return days <= max_days
    except Exception:
        return False
    return False

def validate_dsl(dsl, schema_fields, types_map=None, max_days=7, analyzers_map=None):
    errors = []
    if not isinstance(dsl, dict):
        errors.append("DSL must be an object")
        return False, errors
    allowed_top = {"query", "size", "aggs", "sort"}
    for k in dsl.keys():
        if k not in allowed_top:
            errors.append(f"Unsupported top-level key: {k}")
    allowed_ops_by_type = {
        "keyword": {"term", "match", "wildcard"},
        "text": {"match", "wildcard"},
        "date": {"range", "term"},
        "integer": {"range", "term"},
        "long": {"range", "term"},
        "float": {"range", "term"},
        "double": {"range", "term"},
    }

    def check_fields(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("match", "term", "wildcard"):
                    if isinstance(v, dict):
                        for f in v.keys():
                            if f not in schema_fields:
                                errors.append(f"Unknown field: {f}")
                            t = types_map.get(f) if types_map else None
                            if t and k not in allowed_ops_by_type.get(t, set()):
                                errors.append(f"Operator {k} not allowed for type {t} on field {f}")
                            if k == "wildcard" and types_map and types_map.get(f) not in ("keyword", "text"):
                                errors.append(f"Wildcard only permitted on keyword/text: {f}")
                            if t == "keyword" and k == "match":
                                errors.append("Match not appropriate for keyword fields")
                            if analyzers_map and analyzers_map.get(f):
                                if k == "wildcard":
                                    errors.append("Wildcard not allowed on analyzed text fields")
                elif k == "range":
                    if isinstance(v, dict):
                        for f in v.keys():
                            if f not in schema_fields:
                                errors.append(f"Unknown field: {f}")
                            if types_map and types_map.get(f) not in ("date", "integer", "long", "float", "double"):
                                errors.append(f"Range only on date/numeric: {f}")
                            if f != "@timestamp":
                                errors.append("Date range only allowed on @timestamp")
                            if types_map and types_map.get(f) == "nested":
                                errors.append("Nested field requires nested query context")
                else:
                    check_fields(v)
        elif isinstance(obj, list):
            for item in obj:
                check_fields(item)
    check_fields(dsl.get("query", {}))
    if not has_time_range(dsl):
        errors.append("Missing time range on @timestamp")
    else:
        if not within_max_lookback(dsl, max_days=max_days):
            errors.append("Lookback exceeds maximum")
    size = dsl.get("size")
    if size is not None and (not isinstance(size, int) or size <= 0 or size > 1000):
        errors.append("Invalid size")
    sort = dsl.get("sort")
    if sort:
        try:
            items = sort if isinstance(sort, list) else [sort]
            for it in items:
                if isinstance(it, dict):
                    for f, cfg in it.items():
                        if f not in schema_fields:
                            errors.append(f"Unknown sort field: {f}")
                        t = types_map.get(f) if types_map else None
                        if t not in ("date", "keyword", "text"):
                            errors.append(f"Sort not allowed on field type {t}: {f}")
                        sz = dsl.get("size", 0)
                        if t in ("keyword", "text") and (not dsl.get("aggs") and (sz is None or sz > 100)):
                            errors.append("Sort on text/keyword without aggs and size>100 not allowed")
        except Exception:
            errors.append("Invalid sort specification")
    return len(errors) == 0, errors
