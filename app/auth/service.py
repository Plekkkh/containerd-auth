from datetime import timezone, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import User, ApiToken
from app.auth.tokens import create_jwt, generate_api_token
from app.auth.passwords import hash_password, verify_password


def login(
    db: Session,
    username: str,
    password: str,
    settings: Settings
) -> str:
    user = db.query(User).filter_by(username=username).first()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")

    return create_jwt(user.username, user.role, settings.JWT_SECRET, settings.JWT_TTL_MINUTES)


def create_user(
    db: Session,
    username: str,
    password: str,
    role: str
) -> User:
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(409, "Username already exists")

    user = User(username=username, password_hash=hash_password(password), role=role)
    db.add(user)
    db.flush()
    return user


def change_password(
    db: Session,
    user: User,
    old_password: str,
    new_password: str
) -> None:
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(401, "Wrong password")

    user.password_hash = hash_password(new_password)
    user.tokens_revoked_before = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    db.flush()


def create_api_token(
    db: Session,
    user: User,
    name: str
) -> tuple[ApiToken, str]:
    plain, th = generate_api_token()
    token = ApiToken(user_id=user.id, name=name, token_hash=th)
    db.add(token)
    db.flush()
    return token, plain


def list_tokens(
    db: Session,
    user: User
) -> list[ApiToken]:
    return db.query(ApiToken).filter_by(user_id=user.id).all()


def revoke_token(
    db: Session,
    user: User,
    token_id: str
) -> None:
    token = db.get(ApiToken, token_id)
    if token is None or (token.user_id != user.id and user.role != "admin"):
        raise HTTPException(404, "Token not found")

    db.delete(token)
    db.flush()
