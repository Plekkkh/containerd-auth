import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func

from app.auth import service
from app.db import User, get_db, ContainerOwnership, ImageOwnership, ApiToken, AuditLog
from app.rbac import require_admin
from app.audit import audit

router = APIRouter()


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8)
    role: str = Field(pattern="^(user|admin)$")
    model_config = {"extra": "forbid"}


class UserPatchRequest(BaseModel):
    role: str = Field(pattern="^(user|admin)$")
    model_config = {"extra": "forbid"}


def _resolve(db, username: str) -> User:
    user = db.query(User).filter_by(username=username).first()
    if user is None:
        raise HTTPException(404, "User not found")
    return user


@router.get("/users")
def list_users(
    admin: User = Depends(require_admin),
    db=Depends(get_db)
):
    return [{"username": u.username, "role": u.role} for u in db.query(User).all()]


@router.post("/users", status_code=201)
def create_user(
    body: UserCreateRequest,
    db=Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = service.create_user(db, body.username, body.password, body.role)
    audit(db, current_user.username, "user.create", user.username)
    return {"id": user.id, "username": user.username, "role": user.role}


@router.get("/users/{username}")
def get_user(
    username: str,
    admin: User = Depends(require_admin),
    db=Depends(get_db)
):
    u = _resolve(db, username)
    return {"username": u.username, "role": u.role}


@router.patch("/users/{username}")
def patch_user(
    username: str,
    body: UserPatchRequest,
    admin: User = Depends(require_admin),
    db=Depends(get_db),
):
    target = _resolve(db, username)
    if body.role not in ("user", "admin"):
        raise HTTPException(400, "Role must be 'user' or 'admin'")
    if target.username == admin.username and body.role != "admin":
        raise HTTPException(409, "Cannot demote yourself")
    target.role = body.role
    audit(db, admin.username, "user.role_change", target.username)
    return {"username": target.username, "role": target.role}


@router.delete("/users/{username}", status_code=204)
def delete_user(
    username: str,
    request: Request,
    admin: User = Depends(require_admin),
    db=Depends(get_db),
) -> None:
    target = _resolve(db, username)
    if target.username == admin.username:
        raise HTTPException(409, "cannot delete yourself")

    runtime = request.app.state.runtime

    # 1. Контейнеры юзера: строго-владельческие -> останавливаем и сносим физически.
    for c in db.query(ContainerOwnership).filter_by(owner_id=target.id).all():
        try:
            runtime.remove(c.container_id)
        except Exception:  # рантайм может не знать объект (уже снесён) — не роняем каскад
            logging.getLogger(__name__).warning(
                "cascade: cannot remove container %s", c.container_id, exc_info=True
            )
        db.delete(c)

    # 2. Образы юзера: отвязываем его строки, ref с последней строки удаляем физически.
    links = db.query(ImageOwnership).filter_by(owner_id=target.id).all()
    refs = {l.image_ref for l in links}
    for l in links:
        db.delete(l)
    for ref in refs:
        remaining = (
            db.query(func.count(ImageOwnership.owner_id))
            .filter(ImageOwnership.image_ref == ref)
            .scalar()
        )
        if remaining == 0:
            try:
                runtime.remove_image(ref)
            except Exception:
                logging.getLogger(__name__).warning(
                    "cascade: cannot remove image %s", ref, exc_info=True
                )

    # 3. API-токены юзера
    db.query(ApiToken).filter_by(user_id=target.id).delete()
    db.delete(target)
    audit(db, admin.username, "user.delete", target.username)


@router.get("/log")
def get_log(
    limit: int = 100,
    db=Depends(get_db),
    admin: User = Depends(require_admin)
):
    rows = (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .limit(min(limit, 500))
        .all()
    )
    return [
        {
            "id": r.id,
            "actor": r.actor,
            "action": r.action,
            "resource": r.resource,
            "result": r.result,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        } for r in rows
    ]
