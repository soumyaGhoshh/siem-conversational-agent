
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
import user_store

if __name__ == "__main__":
    user_store.set_user("analyst1", "SecretPassword1!", "analyst")
    user_store.set_user("admin", "AdminPassword1!", "admin")
    print("Users seeded successfully.")
