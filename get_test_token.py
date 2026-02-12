import os
import jwt
import time
from dotenv import load_dotenv

load_dotenv()

def get_token():
    uname = "admin"
    role = "admin"
    exp = int(time.time()) + 3600
    jwt_secret = os.getenv("JWT_SECRET", "SIEM_DEFAULT_FALLBACK_SECRET_CHANGE_ME")
    token = jwt.encode({"sub": uname, "role": role, "exp": exp}, jwt_secret, algorithm="HS256")
    print(token)

if __name__ == "__main__":
    get_token()
