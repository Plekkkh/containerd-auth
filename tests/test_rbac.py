"""Этап B: RBAC + ownership (IDOR / vertical escalation)."""
import pytest


def mk_container(c, headers, name, image="docker.io/library/alpine:3.19"):
    rb = c.post("/images", json={"name": image}, headers=headers)
    r = c.post("/containers", json={"name": name, "image": image}, headers=headers)
    assert r.status_code == 201, r.text
    rb = c.delete(f"/images/{image}", headers=headers)

    return r.json()["id"]


class TestOwnershipHorizontal:
    """user1 vs объекты user2 — горизонтальное нарушение границ."""

    def test_user_sees_only_own_containers(self, client):
        c, h = client
        mk_container(c, h["user1"], "c1")
        mk_container(c, h["user2"], "c2")
        lst = c.get("/containers", headers=h["user1"]).json()
        names = [x["name"] for x in lst]
        assert "c1" in names and "c2" not in names

    def test_admin_sees_all_containers(self, client):
        c, h = client
        mk_container(c, h["user1"], "c1")
        mk_container(c, h["user2"], "c2")
        lst = c.get("/containers", headers=h["admin"]).json()
        assert {"c1", "c2"} <= {x["name"] for x in lst}

    def test_idor_read_foreign_container_403or404(self, client):
        c, h = client
        cid = mk_container(c, h["user1"], "victim")
        r = c.get(f"/containers/{cid}", headers=h["user2"])
        assert r.status_code in (403, 404), "user2 прочитал контейнер user1"

    def test_idor_stop_foreign_container(self, client):
        c, h = client
        cid = mk_container(c, h["user1"], "victim")
        c.post(f"/containers/{cid}/start", headers=h["user1"])
        r = c.post(f"/containers/{cid}/stop", headers=h["user2"])
        assert r.status_code in (403, 404)

    def test_idor_delete_foreign_container(self, client):
        c, h = client
        cid = mk_container(c, h["user1"], "victim")
        r = c.delete(f"/containers/{cid}", headers=h["user2"])
        assert r.status_code in (403, 404)
        # Контейнер должен остаться на месте.
        assert c.get(f"/containers/{cid}", headers=h["user1"]).status_code == 200

    def test_idor_logs_foreign_container(self, client):
        c, h = client
        cid = mk_container(c, h["user1"], "victim")
        r = c.get(f"/containers/{cid}/logs", headers=h["user2"])
        assert r.status_code in (403, 404)

    def test_idor_by_guessing_ids(self, client):
        # Проверка против IDOR по перебору: если id инкрементальные,
        # user2, зная свой id, не должен получить чужой.
        c, h = client
        cid1 = mk_container(c, h["user1"], "a")
        cid2 = mk_container(c, h["user2"], "b")
        if cid1 == cid2:
            pytest.skip("рантайм генерирует коллизии id — не применимо")
        r = c.get(f"/containers/{cid1}", headers=h["user2"])
        assert r.status_code in (403, 404)

    def test_owner_full_lifecycle_on_own_container(self, client):
        c, h = client
        cid = mk_container(c, h["user1"], "mine")
        assert c.post(f"/containers/{cid}/start", headers=h["user1"]).status_code in (200, 201)
        assert c.post(f"/containers/{cid}/stop", headers=h["user1"]).status_code in (200, 201)
        assert c.get(f"/containers/{cid}/logs", headers=h["user1"]).status_code == 200
        assert c.delete(f"/containers/{cid}", headers=h["user1"]).status_code in (200, 204)


class TestVerticalEscalation:
    """user vs admin-эндпоинты."""

    def test_user_cannot_list_users(self, client):
        c, h = client
        assert c.get("/admin/users", headers=h["user1"]).status_code == 403

    def test_user_cannot_create_user(self, client):
        c, h = client
        r = c.post(
            "/admin/users",
            json={"username": "evil", "password": "x", "role": "admin"},
            headers=h["user1"],
        )
        assert r.status_code == 403

    def test_user_cannot_delete_users(self, client):
        c, h = client
        assert c.delete("/admin/users/user2", headers=h["user1"]).status_code == 403

    def test_user_cannot_touch_foreign_container_even_as_admin_action(self, client):
        c, h = client
        cid = mk_container(c, h["user2"], "u2own")
        r = c.delete(f"/containers/{cid}", headers=h["user1"])
        assert r.status_code in (403, 404)

    def test_role_not_trusted_from_user_input(self, client):
        # Попытка.self-эскалации через обычные эндпоинты.
        c, h = client
        r = c.patch("/auth/password", json={"old_password": "Password123!", "new_password": "NewPass456!", "role": "admin"}, headers=h["user1"])
        payload = None
        lst = c.get("/admin/users", headers=h["user1"])
        assert lst.status_code == 403, "role из body запроса дал эскалацию"


class TestAdminPowers:
    def test_admin_can_manage_foreign_container(self, client):
        c, h = client
        cid = mk_container(c, h["user1"], "u1own")
        assert c.post(f"/containers/{cid}/start", headers=h["admin"]).status_code in (200, 201)
        assert c.delete(f"/containers/{cid}", headers=h["admin"]).status_code in (200, 204)

    def test_admin_creates_user_and_user_can_login(self, client):
        c, h = client
        r = c.post(
            "/admin/users",
            json={"username": "user3", "password": "Password123!", "role": "user"},
            headers=h["admin"],
        )
        assert r.status_code == 201
        r = c.post("/auth/login", json={"username": "user3", "password": "Password123!"})
        assert r.status_code == 200

    def test_admin_cannot_demote_self_accidentally_guarded_or_allowed(self, client):
        c, h = client
        r = c.patch("/admin/users/admin", json={"role": "user"}, headers=h["admin"])
        # Дизайн-развилка: либо 400/409 (guard), либо разрешено. Главное — не 500.
        assert r.status_code in (200, 400, 403, 409)


class TestInputValidation:
    def test_container_name_path_traversal_rejected(self, client):
        c, h = client
        for bad in ("../../etc", "a/../b", "../shadow", "name with space", "a;b", "$(id)"):
            r = c.post("/containers", json={"name": bad, "image": "docker.io/library/alpine:3.19"}, headers=h["user1"])
            assert r.status_code in (400, 422), f"принято опасное имя: {bad}"

    def test_privileged_flag_rejected(self, client):
        c, h = client
        r = c.post(
            "/containers",
            json={"name": "p", "image": "docker.io/library/alpine:3.19", "privileged": True},
            headers=h["user1"],
        )
        assert r.status_code in (400, 422), "privileged прошёл — это root backdoor"

    def test_host_network_rejected(self, client):
        c, h = client
        r = c.post(
            "/containers",
            json={"name": "hn", "image": "docker.io/library/alpine:3.19", "host_network": True},
            headers=h["user1"],
        )
        assert r.status_code in (400, 422)

    def test_unknown_image_reference_shape_rejected(self, client):
        c, h = client
        r = c.post("/containers", json={"name": "ok", "image": ""}, headers=h["user1"])
        assert r.status_code in (400, 422)
