"""Общие фикстуры для тестов auth-ядра и RBAC.

Ожидаемый контракт приложения (app/main.py):
  - приложение создаётся фабрикой create_app() (иначе нельзя подменить БД в тестах);
  - конфиг через env:
      APP_DB_PATH        путь к sqlite (для тестов — tmp-файл)
      JWT_SECRET         секрет подписи токенов
      JWT_TTL_MINUTES    TTL access-токена (по умолчанию 15)
      RUNTIME_ADAPTER    "fake" | "containerd" (по умолчанию fake)
  - при RUNTIME_ADAPTER=fake рантайм — in-memory, пустой при старте.

Контракт API:
  POST /auth/login        {username, password} -> {"access_token": ...}
  POST /admin/users        {username, password, role}   (admin) -> 201
  PATCH /auth/password    {old_password, new_password}
  POST  /auth/tokens      {name} -> {"token": "<bearer>", "id": ...}
  GET   /auth/tokens      -> [{id, name, created_at}]
  DELETE /auth/tokens/{id}
  POST   /containers      {name, image} -> 201 {"id": ...}
  GET    /containers      -> [{id, name, image, owner}]  (user: свои; admin: все)
  GET    /containers/{id} / start / stop / DELETE / GET /containers/{id}/logs
  GET    /images          (список; ownership образов — по пуллу/импорту)
  DELETE /images/{ref}
  GET    /admin/users     (admin)
"""
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_factory(tmp_path, monkeypatch):
    """Фабрика приложений: каждый вызов -> свежий клиент с чистой БД."""
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "AdminTest999!")
    monkeypatch.setenv("APP_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("APP_DB_URL", raising=False)
    monkeypatch.setenv("JWT_SECRET", "3199277a63dc8017934e8b5586ee240163a728fbb08a984264df32ab8a56ef46")
    monkeypatch.setenv("RUNTIME_ADAPTER", "fake")

    # Импорт внутри фикстуры, чтобы env применился до создания приложения.
    from app.main import create_app

    created = []

    def _make():
        app = create_app()
        created.append(app)
        return TestClient(app)

    yield _make


@pytest.fixture()
def client(app_factory):
    """Клиент с предзаведёнными аккаунтами.

    Возвращает (client, helpers) где helpers:
      admin_headers / user1_headers / user2_headers — готовые bearer-заголовки.
    Пароли по умолчанию: Password123!  (argon2 обязан это переварить).
    """
    c = app_factory()

    def _login(username: str) -> str:
        r = c.post("/auth/login", json={
            "username": username,
            "password": "AdminTest999!" if username == "admin" else "Password123!"
        })
        assert r.status_code == 200, r.text
        return r.json()["access_token"]


    admin_headers = {"Authorization": f"Bearer {_login(os.environ.get('ADMIN_USERNAME', 'admin'))}"}
    for name in ("user1", "user2"):
        r = c.post(
            "/admin/users",
            json={"username": name, "password": "Password123!", "role": "user"},
            headers=admin_headers,
        )
        assert r.status_code == 201, r.text

    helpers = {
        "admin": {"Authorization": f"Bearer {_login('admin')}"},
        "user1": {"Authorization": f"Bearer {_login('user1')}"},
        "user2": {"Authorization": f"Bearer {_login('user2')}"},
    }
    return c, helpers


def expired_token_for(username: str) -> dict:
    """Не используется напрямую; оставлен как маркер: тесты с просроченным
    токеном должны генерировать его через свой JWT_SECRET (см. test_auth)."""
    return {"Authorization": f"Bearer {username}"}
