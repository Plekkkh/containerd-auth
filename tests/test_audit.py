# tests/test_audit.py
"""Аудит: мутации пишутся в audit_log; read-эндпоинты не пишут.

client-фикстура возвращает (TestClient, helpers). БД — sqlite tmp-файл,
открываем её напрямую через session_factory() с APP_DB_PATH из env.
"""
import pytest

from app.db import AuditLog


def _last(db, action):
    return db.query(AuditLog).filter_by(action=action).order_by(AuditLog.id.desc()).first()


@pytest.fixture()
def ctx(client):
    c, helpers = client
    return c, helpers["user1"], helpers["admin"]


def test_audit_container_create_and_delete(ctx):
    c, h, _ = ctx
    ref = "docker.io/library/alpine:3.19"
    r = c.post("/images", json={"image_ref": ref}, headers=h)
    r = c.post("/containers", json={"name": "aud-c1", "image": "docker.io/library/alpine:3.19"},
               headers=h)
    assert r.status_code == 201, r.text
    r = c.delete("/containers/aud-c1", headers=h)
    assert r.status_code == 200, r.text
    r = c.delete(f"/images/{ref}", headers=h)

    with _db() as db:
        create = _last(db, "container.create")
        assert create is not None and create.resource == "aud-c1" and create.result == "ok"
        delete = _last(db, "container.delete")
        assert delete is not None and delete.resource == "aud-c1"


def _db():
    from app.db import session_factory
    return session_factory()


def test_audit_image_pull_and_delete(ctx):
    c, h, _ = ctx
    ref = "docker.io/library/alpine:3.19"
    r = c.post("/images", json={"image_ref": ref}, headers=h)
    assert r.status_code in (200, 201), r.text
    r = c.delete(f"/images/{ref}", headers=h)
    assert r.status_code == 200, r.text

    with _db() as db:
        pull = _last(db, "image.pull")
        assert pull is not None and pull.resource == ref
        delete = _last(db, "image.delete")
        assert delete is not None and delete.resource == ref


def test_audit_role_change_recorded(ctx):
    c, _, admin = ctx
    r = c.post("/admin/users", json={"username": "victim", "password": "Password123!",
                                     "role": "user"}, headers=admin)
    assert r.status_code == 201, r.text
    r = c.patch("/admin/users/victim", json={"role": "admin"}, headers=admin)
    assert r.status_code == 200, r.text

    with _db() as db:
        rec = _last(db, "user.role_change")
        assert rec is not None and rec.resource == "victim"
        assert rec.actor == "admin"


def test_audit_user_delete_recorded(ctx):
    c, _, admin = ctx
    r = c.post("/admin/users", json={"username": "goner", "password": "Password123!",
                                     "role": "user"}, headers=admin)
    assert r.status_code == 201, r.text
    r = c.delete("/admin/users/goner", headers=admin)
    assert r.status_code == 204, r.text

    with _db() as db:
        rec = _last(db, "user.delete")
        assert rec is not None and rec.resource == "goner"
        assert rec.actor == "admin"


def test_audit_reads_not_logged(ctx):
    c, h, _ = ctx
    with _db() as db:
        baseline = db.query(AuditLog).count()  # тут уже user.create от фикстуры

    c.get("/containers", headers=h)
    c.get("/images", headers=h)
    c.get("/admin/users", headers=h)

    with _db() as db:
        assert db.query(AuditLog).count() == baseline
