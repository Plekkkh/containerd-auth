from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import service
from app.db import get_db, User
from app.rbac import get_current_user, get_settings

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str
    model_config = {"extra": "forbid"}


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
    model_config = {"extra": "forbid"}


class ApiTokenCreateRequest(BaseModel):
    name: str
    model_config = {"extra": "forbid"}


@router.post("/login")
def login(
    body: LoginRequest,
    db=Depends(get_db),
    settings=Depends(get_settings)
):
    return {"access_token": service.login(db, body.username, body.password, settings)}


@router.patch("/password")
def change_password(
    body: PasswordChangeRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.old_password == body.new_password:
        raise HTTPException(400, "new password must differ from old")

    service.change_password(db, current_user, body.old_password, body.new_password)
    return {"status": "password changed"}


@router.post("/tokens", status_code=201)
def create_api_token(
    body: ApiTokenCreateRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    token, plain = service.create_api_token(db, current_user, body.name)
    return {"id": token.id, "token": plain}


@router.delete("/tokens/{token_id}")
def revoke_api_token(
    token_id: str,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.revoke_token(db, current_user, token_id)
    return {"status": "token revoked"}