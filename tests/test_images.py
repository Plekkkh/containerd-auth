# tests/test_images.py
"""Семантика образов: shared-ref модель, refcount-удаление, RBAC."""
import pytest

REF = "docker.io/library/alpine:3.19"


@pytest.fixture()
def h(client):
    """(client, helpers) из conftest; helpers уже содержит admin/user1/user2."""
    c, helpers = client
    return helpers


@pytest.fixture()
def c(client):
    c, helpers = client
    return c


def test_pull_is_idempotent_across_users(c, h):
    """user1 пуллит; user2 пуллит тот же ref — не 409, у каждого своя ссылка."""
    r1 = c.post("/images", json={"image_ref": REF}, headers=h["user1"])
    assert r1.status_code in (200, 201), r1.text
    r2 = c.post("/images", json={"image_ref": REF}, headers=h["user2"])
    assert r2.status_code in (200, 201), r2.text

    # Каждый видит ref у себя
    l1 = c.get("/images", headers=h["user1"]).json()
    l2 = c.get("/images", headers=h["user2"]).json()
    assert REF in [i["ref"] for i in l1]
    assert REF in [i["ref"] for i in l2]


def test_list_images_scoped_by_owner(c, h):
    other = "docker.io/library/busybox:1.36"
    c.post("/images", json={"image_ref": REF}, headers=h["user1"])
    c.post("/images", json={"image_ref": other}, headers=h["user2"])

    l1 = [i["ref"] for i in c.get("/images", headers=h["user1"]).json()]
    l2 = [i["ref"] for i in c.get("/images", headers=h["user2"]).json()]
    assert REF in l1 and other not in l1
    assert other in l2 and REF not in l2

    l_admin = [i["ref"] for i in c.get("/images", headers=h["admin"]).json()]
    assert REF in l_admin and other in l_admin


def test_delete_detaches_only_own_link(c, h):
    """user2 удаляет свою ссылку — образ продолжает жить для user1."""
    c.post("/images", json={"image_ref": REF}, headers=h["user1"])
    c.post("/images", json={"image_ref": REF}, headers=h["user2"])

    r = c.delete(f"/images/{REF}", headers=h["user2"])
    assert r.status_code == 200, r.text

    # user1 всё ещё видит и может использовать образ
    l1 = [i["ref"] for i in c.get("/images", headers=h["user1"]).json()]
    assert REF in l1
    # Создание контейнера из образа по-прежнему работает у user1
    rc = c.post(
        "/containers",
        json={"name": "from-alive-image", "image": REF},
        headers=h["user1"],
    )
    assert rc.status_code == 201, rc.text


def test_last_owner_delete_removes_image_from_runtime(c, h):
    """Когда последняя ссылка отвязана — образ физически удаляется из рантайма."""
    c.post("/images", json={"image_ref": REF}, headers=h["user1"])
    c.post("/images", json={"image_ref": REF}, headers=h["user2"])

    c.delete(f"/images/{REF}", headers=h["user1"])
    c.delete(f"/images/{REF}", headers=h["user2"])

    # Ни у кого не осталось ссылки
    for who in ("user1", "user2"):
        refs = [i["ref"] for i in c.get("/images", headers=h[who]).json()]
        assert REF not in refs


def test_user_cannot_see_or_delete_foreign_image(c, h):
    """IDOR по образам: чужой ref — 404 (не раскрываем существование)."""
    c.post("/images", json={"image_ref": REF}, headers=h["user1"])

    r = c.delete(f"/images/{REF}", headers=h["user2"])
    assert r.status_code in (403, 404), r.text
    l2 = [i["ref"] for i in c.get("/images", headers=h["user2"]).json()]
    assert REF not in l2

    # Образ не пострадал
    l1 = [i["ref"] for i in c.get("/images", headers=h["user1"]).json()]
    assert REF in l1


def test_admin_can_delete_image_entirely(c, h):
    """Админ сносит образ целиком: все ссылки + рантайм."""
    c.post("/images", json={"image_ref": REF}, headers=h["user1"])
    c.post("/images", json={"image_ref": REF}, headers=h["user2"])

    r = c.delete(f"/images/{REF}", headers=h["admin"])
    assert r.status_code == 200, r.text

    for who in ("user1", "user2", "admin"):
        refs = [i["ref"] for i in c.get("/images", headers=h[who]).json()]
        assert REF not in refs


def test_container_created_from_pulled_image(c, h):
    """Happy-path: pull -> создать контейнер из образа."""
    c.post("/images", json={"image_ref": REF}, headers=h["user1"])
    r = c.post(
        "/containers",
        json={"name": "c-alpine", "image": REF},
        headers=h["user1"],
    )
    assert r.status_code == 201, r.text
    assert r.json()["id"]
