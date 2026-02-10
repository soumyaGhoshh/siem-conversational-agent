import sqlite3
import os
import time

DB_PATH = os.getenv("AUDIT_DB_PATH", "audit.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, user TEXT, idx TEXT, hits INTEGER, duration_ms INTEGER, query_json TEXT)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS saved_searches (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, user TEXT, idx TEXT, query_json TEXT, created_ts INTEGER)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, user TEXT, idx TEXT, threshold INTEGER, time_window TEXT, last_trigger_ts INTEGER, created_ts INTEGER)"
    )
    conn.commit()
    conn.close()

def log_query(user, idx, hits, duration_ms, query_json):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO queries (ts, user, idx, hits, duration_ms, query_json) VALUES (?, ?, ?, ?, ?, ?)",
        (int(time.time()), user, idx, int(hits), int(duration_ms), query_json),
    )
    conn.commit()
    conn.close()

def list_queries(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ts, user, idx, hits, duration_ms FROM queries ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
def export_queries_json(signing_key=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ts, user, idx, hits, duration_ms, query_json FROM queries ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    data = [{"ts": r[0], "user": r[1], "idx": r[2], "hits": r[3], "duration_ms": r[4], "query_json": r[5]} for r in rows]
    if signing_key:
        import hmac, hashlib, json as _json
        payload = _json.dumps(data, separators=(",", ":"))
        sig = hmac.new(signing_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return {"data": data, "signature": sig}
    return {"data": data}

def prune_old_queries(max_days=30):
    cutoff = int(time.time()) - max_days * 86400
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM queries WHERE ts < ?", (cutoff,))
    conn.commit()
    conn.close()

def save_search(name, user, idx, query_json):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO saved_searches (name, user, idx, query_json, created_ts) VALUES (?, ?, ?, ?, ?)",
        (name, user, idx, query_json, int(time.time())),
    )
    conn.commit()
    conn.close()

def list_saved_searches(user=None, limit=100):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if user:
        cur.execute("SELECT id, name, idx FROM saved_searches WHERE user=? ORDER BY id DESC LIMIT ?", (user, limit))
    else:
        cur.execute("SELECT id, name, idx FROM saved_searches ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_saved_search(search_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT query_json, idx FROM saved_searches WHERE id=?", (search_id,))
    row = cur.fetchone()
    conn.close()
    return row

def add_alert(name, user, idx, threshold, time_window):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (name, user, idx, threshold, time_window, last_trigger_ts, created_ts) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, user, idx, int(threshold), time_window, 0, int(time.time())),
    )
    conn.commit()
    conn.close()

def list_alerts(user=None, limit=100):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if user:
        cur.execute("SELECT id, name, idx, threshold, time_window, last_trigger_ts FROM alerts WHERE user=? ORDER BY id DESC LIMIT ?", (user, limit))
    else:
        cur.execute("SELECT id, name, idx, threshold, time_window, last_trigger_ts FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_alert_triggered(alert_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE alerts SET last_trigger_ts=? WHERE id=?", (int(time.time()), int(alert_id)))
    conn.commit()
    conn.close()
