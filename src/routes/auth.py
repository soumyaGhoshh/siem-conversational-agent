import os
import time
import jwt
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import user_store

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

TOKEN_BLACKLIST = set()

def require_auth(request: Request):
    token = request.headers.get("Authorization", "")
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    val = token.replace("Bearer ", "").strip()
    if val in TOKEN_BLACKLIST:
        raise HTTPException(status_code=401, detail="Token revoked")
    try:
        jwt_secrets_env = os.getenv("JWT_SECRETS")
        jwt_secret_env = os.getenv("JWT_SECRET")
        if jwt_secrets_env:
            secrets = [s.strip() for s in jwt_secrets_env.split(",") if s.strip()]
        elif jwt_secret_env:
            secrets = [jwt_secret_env]
        else:
            # Fallback to a warning and a slightly better default than 'devsecret'
            # but ideally we should fail here in production.
            logger.warning("JWT_SECRET not set, using fallback. Run src/gen_secret.py to fix.")
            secrets = ["SIEM_DEFAULT_FALLBACK_SECRET_CHANGE_ME"]
        
        payload = None
        for sec in secrets:
            try:
                payload = jwt.decode(val, sec, algorithms=["HS256"], options={"require": ["exp"]})
                break
            except Exception as e:
                logger.debug(f"require_auth: failed to decode with secret: {e}")
                continue
        if payload is None:
            raise Exception("invalid")
        uname = payload.get("sub")
        role = payload.get("role", "analyst")
        return uname, role
    except Exception as e:
        logger.error(f"require_auth error: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/login")
async def login(request: Request):
    body = await request.json()
    uname = body.get("username")
    pwd = body.get("password")
    logger.info(f"Login attempt for user: {uname}")
    ok, role = user_store.verify_user(uname, pwd)
    if not ok:
        logger.warning(f"Login failed for user: {uname}")
        return JSONResponse(status_code=401, content={"error": "Invalid credentials"})
    
    exp = int(time.time()) + int(os.getenv("JWT_EXP_SECONDS", "3600")) # 1 hour default
    jwt_secret = os.getenv("JWT_SECRET", "SIEM_DEFAULT_FALLBACK_SECRET_CHANGE_ME")
    token = jwt.encode({"sub": uname, "role": role, "exp": exp}, jwt_secret, algorithm="HS256")
    return {"token": token, "role": role}

@router.post("/refresh")
async def refresh(request: Request):
    body = await request.json()
    old = body.get("token", "")
    try:
        jwt_secret = os.getenv("JWT_SECRET", "SIEM_DEFAULT_FALLBACK_SECRET_CHANGE_ME")
        payload = jwt.decode(old, jwt_secret, algorithms=["HS256"], options={"verify_exp": False})
        uname = payload.get("sub")
        role = payload.get("role", "analyst")
        exp = int(time.time()) + int(os.getenv("JWT_EXP_SECONDS", "3600"))
        new_token = jwt.encode({"sub": uname, "role": role, "exp": exp}, jwt_secret, algorithm="HS256")
        return {"token": new_token}
    except Exception:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})

@router.post("/logout")
async def logout(request: Request):
    body = await request.json()
    tok = body.get("token", "")
    TOKEN_BLACKLIST.add(tok)
    return {"ok": True}
