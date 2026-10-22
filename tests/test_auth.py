"""Этап A: аутентификация и управление учёткой."""
import base64
import json
import time


def _decode_jwt_payload(token: str) -> dict:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


class TestLogin:
    def test_login_ok_returns_jwt(self, client):
        c, h = client
        r = c.post("/auth/login", json={"username": "user1", "password": "Password123!"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        assert token.count(".") == 2, "это не JWT"

    def test_login_bad_password_401(self, client):
        c, h = client
        r = c.post("/auth/login", json={"username": "user1", "password": "wrong"})
        assert r.status_code == 401

    def test_login_unknown_user_401(self, client):
        c, h = client
        r = c.post("/auth/login", json={"username": "ghost", "password": "whatever"})
        assert r.status_code == 401

    def test_jwt_contains_sub_and_role_and_exp(self, client):
        c, h = client
        token = c.post("/auth/login", json={"username": "admin", "password": "AdminTest999!"}).json()["access_token"]
        payload = _decode_jwt_payload(token)
        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"
        assert payload["exp"] > time.time()

    def test_login_no_rate_limit_lockout_hint(self, client):
        # Smoke: 5 неверных паролей подряд не должны уронить сервер (500).
        c, h = client
        for _ in range(5):
            r = c.post("/auth/login", json={"username": "user1", "password": "bad"})
            assert r.status_code in (401, 429)


class TestProtectedEndpoints:
    def test_no_token_401(self, client):
        c, h = client
        assert c.get("/containers").status_code == 401

    def test_garbage_token_401(self, client):
        c, h = client
        r = c.get("/containers", headers={"Authorization": "Bearer not.a.jwt"})
        assert r.status_code == 401

    def test_tampered_signature_401(self, client):
        c, h = client
        token = c.post("/auth/login", json={"username": "user1", "password": "Password123!"}).json()["access_token"]
        header, payload, sig = token.split(".")
        forged = f"{header}.{payload}.AAAA{sig[4:]}"
        r = c.get("/containers", headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401

    def test_expired_token_401(self, client, tmp_path, monkeypatch):
        # Генерируем токен с exp в прошлом тем же секретом.
        c, h = client
        import jwt
        settings = c.app.state.settings  # ожидается pydantic-settings-объект с JWT_SECRET

        expired = jwt.encode(
            {"sub": "user1", "role": "user", "exp": int(time.time()) - 60},
            settings.JWT_SECRET,
            algorithm="HS256",
        )
        r = c.get("/containers", headers={"Authorization": f"Bearer {expired}"})
        assert r.status_code == 401


class TestPasswordChange:
    def test_change_password_ok_and_old_invalid(self, client):
        c, h = client
        r = c.patch(
            "/auth/password",
            json={"old_password": "Password123!", "new_password": "NewPass456!"},
            headers=h["user1"],
        )
        assert r.status_code == 200
        r = c.post("/auth/login", json={"username": "user1", "password": "Password123!"})
        assert r.status_code == 401
        r = c.post("/auth/login", json={"username": "user1", "password": "NewPass456!"})
        assert r.status_code == 200

    def test_change_password_wrong_old_403(self, client):
        c, h = client
        r = c.patch(
            "/auth/password",
            json={"old_password": "wrong", "new_password": "NewPass456!"},
            headers=h["user1"],
        )
        assert r.status_code in (401, 403)

    def test_passwords_stored_hashed(self, client):
        c, h = client
        import sqlite3
        settings = c.app.state.settings

        db = sqlite3.connect(settings.APP_DB_PATH)
        rows = db.execute("SELECT password_hash FROM users").fetchall()
        db.close()
        assert rows, "нет пользователей в БД"
        for (ph,) in rows:
            assert "Password123!" not in ph
            assert ph.startswith("$argon2"), f"ожидается argon2-хеш, получено: {ph[:20]}"


class TestApiTokens:
    def test_create_token_and_use_it(self, client):
        c, h = client
        r = c.post("/auth/tokens", json={"name": "ci"}, headers=h["user1"])
        assert r.status_code == 201
        tok = r.json()["token"]
        r = c.get("/containers", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200

    def test_token_not_stored_plaintext(self, client):
        c, h = client
        tok = c.post("/auth/tokens", json={"name": "ci"}, headers=h["user1"]).json()["token"]
        import sqlite3
        settings = c.app.state.settings

        db = sqlite3.connect(settings.APP_DB_PATH)
        raw = "\n".join(str(row) for row in db.execute("SELECT * FROM api_tokens").fetchall())
        db.close()
        assert tok not in raw, "API-токен хранится в открытом виде"

    def test_revoke_token_invalidates_it(self, client):
        c, h = client
        tok = c.post("/auth/tokens", json={"name": "ci"}, headers=h["user1"]).json()
        tid = tok["id"]
        r = c.delete(f"/auth/tokens/{tid}", headers=h["user1"])
        assert r.status_code == 200
        r = c.get("/containers", headers={"Authorization": f"Bearer {tok['token']}"})
        assert r.status_code == 401

    def test_cannot_delete_foreign_token(self, client):
        c, h = client
        tok = c.post("/auth/tokens", json={"name": "mine"}, headers=h["user1"]).json()
        r = c.delete(f"/auth/tokens/{tok['id']}", headers=h["user2"])
        assert r.status_code in (403, 404)

    def test_password_change_invalidates_tokens(self, client):
        # После смены пароля ранее выданные долгоживущие токены должны отзывать
        # (иначе смена пароля бессмысленна против утечки). Допустимый дизайн:
        # либо все токены ревокаются, либо password_hash входит в claim/token.
        c, h = client
        tok = c.post("/auth/tokens", json={"name": "ci"}, headers=h["user1"]).json()["token"]
        c.patch(
            "/auth/password",
            json={"old_password": "Password123!", "new_password": "NewPass456!"},
            headers=h["user1"],
        )
        r = c.get("/containers", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401, "после смены пароля старый API-токен продолжает работать — уязвимость"
