import re

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field

from app.db import ContainerOwnership, get_db, User, ImageOwnership
from app.rbac import get_current_user
from app.runtime.base import RuntimeUnavailable, RuntimeConflict
from app.audit import audit

router = APIRouter()

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class ContainerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    image: str = Field(min_length=1, max_length=256)

    model_config = {"extra": "forbid"}


def _get_owned_container(db, user: User, container_id: str):
    rec = db.get(ContainerOwnership, container_id)
    if rec is None:
        raise HTTPException(404, "container not found")
    if rec.owner_id != user.id and not user.role == "admin":
        raise HTTPException(404, "container not found")
    return rec


@router.post("", status_code=201)
def create_container(
    body: ContainerCreate,
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    if not _NAME_RE.match(body.name):
        raise HTTPException(422, "Invalid container name")
    if db.get(ContainerOwnership, body.name) is not None:
        raise HTTPException(409, "Name already taken")

    owned = (
        db.query(ImageOwnership)
        .filter_by(image_ref=body.image, owner_id=user.id)
        .first()
    )
    if owned is None and user.role != "admin":
        raise HTTPException(403, "Image not owned by you")

    runtime = request.app.state.runtime
    try:
        container_id = runtime.create_container(body.name, body.image)
    except RuntimeConflict:
        raise HTTPException(409, "Name already taken")
    except RuntimeUnavailable:
        raise HTTPException(502, "Container runtime error")

    db.add(ContainerOwnership(container_id=container_id, owner_id=user.id))
    audit(db, user.username, "container.create", container_id)
    return {"id": container_id, "name": body.name, "image": body.image}


@router.get("")
def list_containers(
    request: Request,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    runtime = request.app.state.runtime
    all_c = {c["id"]: c for c in runtime.list_containers()}
    rows = db.query(ContainerOwnership).all()
    if user.role != "admin":
        rows = [r for r in rows if r.owner_id == user.id]
    return [
        {**all_c[r.container_id], "owner": r.owner_id}
        for r in rows
        if r.container_id in all_c
    ]


@router.get("/{container_id}")
def get_container(
    container_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    _get_owned_container(db, user, container_id)
    return request.app.state.runtime.get_container(container_id)


@router.post("/{container_id}/start")
def start_container(
    container_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    _get_owned_container(db, user, container_id)
    request.app.state.runtime.start(container_id)
    audit(db, user.username, "container.start", container_id)
    return {"status": "started"}


@router.post("/{container_id}/stop")
def stop_container(
    container_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    _get_owned_container(db, user, container_id)
    request.app.state.runtime.stop(container_id)
    audit(db, user.username, "container.stop", container_id)
    return {"status": "stopped"}


@router.get("/{container_id}/logs")
def container_logs(
    container_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    _get_owned_container(db, user, container_id)
    return {"logs": request.app.state.runtime.logs(container_id)}


@router.delete("/{container_id}")
def delete_container(
    container_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    _get_owned_container(db, user, container_id)
    request.app.state.runtime.remove(container_id)
    db.delete(db.get(ContainerOwnership, container_id))
    audit(db, user.username, "container.delete", container_id)
    return {"status": "deleted"}
