import re

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import func

from app.db import get_db, ImageOwnership, User
from app.rbac import get_current_user
from app.audit import audit
from app.runtime.base import RuntimeNotFound, RuntimeUnavailable

router = APIRouter()

_IMAGE_RE = re.compile(
    r"^(?:[a-z0-9]+(?:[._-][a-z0-9]+)*(?::[0-9]+)?/)?"      # registry[:port]/
    r"[a-z0-9]+(?:[._-][a-z0-9]+)*"                         # repo
    r"(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*"                   # namespace-путь
    r"(?::[\w.-]+)?"                                        # :tag
    r"(?:@sha256:[a-f0-9]{64})?$"                           # @digest
)

class ImagePull(BaseModel):
    image_ref: str = Field(min_length=1, max_length=256)

    model_config = {"extra": "forbid"}


def _valid_ref(ref: str) -> bool:
    return bool(_IMAGE_RE.match(ref))


@router.post("")
def pull_image(
    body: ImagePull,
    request: Request,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    ref = body.image_ref
    if not _valid_ref(ref):
        raise HTTPException(422, "Invalid image reference")

    row = db.get(ImageOwnership, (ref, user.id))
    if row is not None:
        return {"image": ref, "status": "already-present"}

    try:
        request.app.state.runtime.pull_image(ref)
    except RuntimeNotFound:
        raise HTTPException(404, "Image not found in registry")
    except RuntimeUnavailable:
        raise HTTPException(502, "Image registry error")

    db.add(ImageOwnership(image_ref=ref, owner_id=user.id))
    audit(db, user.username, "image.pull", ref)
    return {"image": ref, "status": "pulled"}


@router.get("")
def list_images(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    q = db.query(ImageOwnership)
    if user.role != "admin":
        q = q.filter_by(owner_id=user.id)
    return [{"ref": r.image_ref, "owner": r.owner_id} for r in q.all()]


@router.delete("/{image_ref:path}")
def delete_image(
    image_ref: str,
    request: Request,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    if not _valid_ref(image_ref):
        raise HTTPException(422, "Invalid image reference")

    runtime = request.app.state.runtime

    if user.role == "admin":
        rows = db.query(ImageOwnership).filter_by(image_ref=image_ref).all()
        if not rows:
            raise HTTPException(404, "Image not found")
        for r in rows:
            db.delete(r)
        runtime.remove_image(image_ref)
        audit(db, user.username, "image.delete", image_ref)
        return {"status": "deleted", "detached": len(rows)}

    row = db.get(ImageOwnership, (image_ref, user.id))
    if row is None:
        raise HTTPException(404, "Image not found")

    db.delete(row)
    remaining = (
        db.query(func.count(ImageOwnership.owner_id))
        .filter(ImageOwnership.image_ref == image_ref)
        .scalar()
    )
    if remaining == 0:
        runtime.remove_image(image_ref)
    audit(db, user.username, "image.delete", image_ref)
    return {"status": "deleted", "detached": 1}

