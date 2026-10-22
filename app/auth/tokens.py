import hashlib
import secrets
from datetime import datetime, timezone, timedelta

import jwt

ALG = "HS256"


def create_jwt(
    user_id: str,
    role: str,
    secret: str,
    ttl_minutes: int,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
    }
    return jwt.encode(payload, secret, algorithm=ALG)


def decode_jwt(
    token: str,
    secret: str,
) -> dict | None:
    try:
        return jwt.decode(token, secret, algorithms=[ALG])
    except jwt.PyJWTError:
        return None


def generate_api_token() -> tuple[str, str]:
    plain = secrets.token_urlsafe(32)
    return plain, hash_token(plain)


def hash_token(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()
