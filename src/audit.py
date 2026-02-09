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
        "CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, user TEXT, idx TEXT, threshold INTEGER, created_ts INTEGER)"
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

def add_alert(name, user, idx, threshold):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (name, user, idx, threshold, created_ts) VALUES (?, ?, ?, ?, ?)",
        (name, user, idx, int(threshold), int(time.time())),
    )
    conn.commit()
    conn.close()

def list_alerts(user=None, limit=100):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if user:
        cur.execute("SELECT id, name, idx, threshold FROM alerts WHERE user=? ORDER BY id DESC LIMIT ?", (user, limit))
    else:
        cur.execute("SELECT id, name, idx, threshold FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
