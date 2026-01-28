#!/data/data/com.termux/files/usr/bin/env python3
"""
Authentication helpers (hardened):
- create_user(engine, username, password, role)
- authenticate_user(engine, username, password)
- create_access_token(payload, secret, expire)
- verify_token(token, secret)
- revoke_token(engine, jti)
This module intentionally accepts an engine or Session context rather than creating a DB engine,
to avoid circular imports.
"""
import time
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlmodel import select
from models import User, RevokedToken
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_user(engine, username: str, password: str, role: str = "operator"):
    from sqlmodel import Session
    with Session(engine) as s:
        existing = s.exec(select(User).where(User.username == username)).first()
        if existing:
            raise RuntimeError("User exists")
        u = User(username=username, pw_hash=hash_password(password), role=role)
        s.add(u); s.commit()

def authenticate_user(engine, username: str, password: str) -> Optional[User]:
    from sqlmodel import Session
    with Session(engine) as s:
        u = s.exec(select(User).where(User.username == username)).first()
        if not u:
            return None
        if not verify_password(password, u.pw_hash):
            return None
        return u

def create_access_token(data: dict, secret: str, algorithm: str = "HS256", expires_in: int = 3600) -> str:
    payload = data.copy()
    payload["exp"] = int(time.time()) + int(expires_in)
    # include a unique jti for revocation support
    import uuid
    payload["jti"] = uuid.uuid4().hex
    return jwt.encode(payload, secret, algorithm=algorithm)

def verify_token(engine, token: str, secret: str, algorithms: list[str] = ["HS256"]):
    """
    Verify token and check it's not revoked. Returns payload or raise.
    """
    from sqlmodel import Session
    try:
        payload = jwt.decode(token, secret, algorithms=algorithms)
    except JWTError as e:
        raise RuntimeError(f"Invalid token: {e}")
    jti = payload.get("jti")
    if not jti:
        raise RuntimeError("Missing jti in token")
    with Session(engine) as s:
        entry = s.exec(select(RevokedToken).where(RevokedToken.jti == jti)).first()
        if entry:
            raise RuntimeError("Token revoked")
    return payload

def revoke_token(engine, jti: str):
    from sqlmodel import Session
    with Session(engine) as s:
        r = RevokedToken(jti=jti)
        s.add(r); s.commit()