
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
import user_store
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    print(f"USERS_PATH: {os.getenv('USERS_PATH')}")
    ok, role = user_store.verify_user("analyst1", "SecretPassword1!")
    print(f"Verify analyst1: {ok}, {role}")
    ok, role = user_store.verify_user("admin", "AdminPassword1!")
    print(f"Verify admin: {ok}, {role}")
