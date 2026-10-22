from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import Settings
from app.db import get_db, User, ApiToken
from app.auth.tokens import decode_jwt, hash_token

bearer = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db=Depends(get_db),
    settings: Settings = Depends(get_settings)
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing credentials")

    token = credentials.credentials

    payload = decode_jwt(token, settings.JWT_SECRET)
    user = None
    if payload is not None:
        user = db.query(User).filter_by(username=payload["sub"]).first()
    else:
        token_hash = hash_token(token)
        api_token = db.query(ApiToken).filter_by(token_hash=token_hash).first()
        if api_token:
            user = db.get(User, api_token.user_id)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    if user.tokens_revoked_before:
        if payload is not None:
            issued = datetime.fromtimestamp(payload["iat"], tz=timezone.utc).replace(tzinfo=None, microsecond=0)
            if issued < user.tokens_revoked_before.replace(microsecond=0):
                raise HTTPException(status_code=401, detail="Token revoked")
        elif api_token.created_at.replace(tzinfo=None) <= user.tokens_revoked_before:
            raise HTTPException(status_code=401, detail="Token revoked")

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user