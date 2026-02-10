import os
import json
import bcrypt
from dotenv import load_dotenv

# Load .env from root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

USERS_PATH = os.getenv("USERS_PATH", os.path.join(os.path.dirname(__file__), "users.json"))
print(f"Resetting credentials in {USERS_PATH}...")

def set_user(username, password, role="analyst"):
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            users = json.load(f)
    else:
        users = {}
        
    salt = bcrypt.gensalt()
    h = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    users[username] = {"password_hash": h, "role": role}
    
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f)

set_user("analyst1", "changeme", role="analyst")
print("Reset analyst1 to 'changeme'")

set_user("admin", "admin123", role="admin")
print("Reset admin to 'admin123'")

print("Credentials reset complete.")
