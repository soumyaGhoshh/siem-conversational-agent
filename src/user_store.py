import os
import json
import bcrypt
import logging

logger = logging.getLogger(__name__)

USERS_PATH = os.getenv("USERS_PATH", "users.json")

def load_users():
    try:
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def verify_user(username, password):
    users = load_users()
    # Using print for immediate terminal feedback as logger might not be configured in this module
    print(f"DEBUG: verify_user: checking {username} in {list(users.keys())}")
    u = users.get(username)
    if not u:
        print(f"DEBUG: verify_user: user {username} not found")
        return False, None
    hpw = u.get("password_hash")
    if not hpw:
        print(f"DEBUG: verify_user: no password_hash for {username}")
        return False, None
    try:
        # Important: password.encode('utf-8') for hashing/checking
        ok = bcrypt.checkpw(password.encode("utf-8"), hpw.encode("utf-8"))
        print(f"DEBUG: verify_user: bcrypt check for {username}: {ok}")
    except Exception as e:
        print(f"DEBUG: verify_user: bcrypt error: {e}")
        return False, None
    if not ok:
        return False, None
    return True, u.get("role", "analyst")

def set_user(username, password, role="analyst"):
    users = load_users()
    salt = bcrypt.gensalt()
    h = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    users[username] = {"password_hash": h, "role": role}
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f)
