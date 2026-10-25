# containerd-auth — шлюз авторизации к containerd

[![tests](https://img.shields.io/badge/tests-49%20passed-brightgreen)](#тестирование)
[![bandit](https://img.shields.io/badge/SAST-bandit%20%2B%20semgrep-2ea44f)](#тестирование-безопасности)
[![pip-audit](https://img.shields.io/badge/deps-pip--audit%20clean-2ea44f)](#тестирование-безопасности)
[![OWASP ZAP](https://img.shields.io/badge/DAST-ZAP%20120%20PASS-blue)](#тестирование-безопасности)
[![python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.159.1-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![containerd](https://img.shields.io/badge/containerd-2.x-5C2D91)](https://containerd.io)

FastAPI-шлюз, закрывающий containerd 2.x от прямого доступа. Пользователи работают со своими образами и контейнерами через REST API; разграничение — RBAC + модель владения. Слой containerd недоступен по сети: единственная точка входа — шлюз (TLS, порт 8443).

> **Статус:** учебный проект в рамках курса DevSecOps. Не предназначен для использования в production без доработки — см. [Ограничения](#ограничения).

## Архитектура

```
Windows-клиент (curl / Swagger UI / demo.ps1)
        │  HTTPS (TLS 8443, self-signed)
        ▼
FastAPI Gateway (uvicorn, VM Ubuntu 24.04)
  ├── JWT + argon2, bearer API-токены (sha256 в БД)
  ├── RBAC: user / admin + проверка владения ресурсом
  ├── Audit log (запись в БД, чтения не логируются)
  ├── Security headers middleware (HSTS, CSP, nosniff, …)
  └── Runtime adapter (ABC) ──── unix socket ────► containerd 2.x
```

- `app/runtime/base.py` объявляет ABC-контракт `Runtime` с доменными исключениями (`RuntimeNotFound`, `RuntimeUnavailable`). Реализация `ContainerdRuntime` ходит в containerd по gRPC (unix socket, namespace `containerd-auth`), для тестов используется `FakeRuntime` — роутеры не знают о gRPC.
- containerd слушает только локальный unix-сокет; наружу торчит один HTTPS-порт шлюза.
-  `ImageOwnership` — оверлей поверх дедуплицированного content-addressable store containerd. Физическое удаление образа происходит только тогда, когда владельцев не остаётся.

## Модель безопасности

| Механизм         | Реализация                                                                                            |
|------------------|-------------------------------------------------------------------------------------------------------|
| Аутентификация   | JWT (HS256, TTL 15 мин), пароли — argon2                                                              |
| API-токены       | bearer-токены, в БД только sha256-хэш; массовый отзыв через `tokens_revoked_before`                   |
| Авторизация      | RBAC (`user`/`admin`), пользователь видит и меняет только свои ресурсы                                |
| Anti-enumeration | Чужой и несуществующий ресурс — одинаковый 404 без деталей                                            |
| Аудит            | Таблица `AuditLog`, все мутирующие операции; чтения не логируются                                     |
| Заголовки        | HSTS, CSP, nosniff, X-Frame-Options DENY, Permissions-Policy, COEP, no-store                          |
| Ошибки runtime   | gRPC-ошибки транслируются в 404/502, внутренние — 500 без утечки деталей                              |
| Секреты          | При `DEBUG=false` валидатор настроек отклоняет запуск со стандартными `JWT_SECRET` / `ADMIN_PASSWORD` |

Администратор управляет пользователями и видит все ресурсы; `GET /admin/audit` (admin-only) отдаёт журнал операций.

### Токены и сессии

- Refresh-токенов нет — это архитектурное решение. JWT живёт 15 минут; для долгих операций и автоматизации используются API-токены (`POST /auth/tokens`).
- В БД хранится только sha256-хэш API-токена; исходное значение показывается один раз при создании.
- Смена пароля (`PATCH /auth/password`) инвалидирует все выданные JWT и API-токены пользователя.
- Отдельный токен можно отозвать через `DELETE /auth/tokens/{token_id}`.

### Аудит: fail-open

Если запись в аудит-лог не удалась (БД недоступна, диск заполнен, исключение внутри логгера), основная операция всё равно выполняется, а сбой аудита пишется в stderr через `logger.exception`.

Это осознанный компромисс в пользу доступности: проблемы аудита не должны блокировать работу пользователей. Цена — возможность выполнения мутирующей операции без записи в журнал. В production-среде стоит либо перейти на fail-closed для критичных операций, либо мониторить ошибки аудита в логах и поднимать алерт.

## Ограничения

Проект учебный, поэтому ряд вещей сделан намеренно упрощённо:

- **Нет rate limiting и защиты от брутфорса** логина — при публичном развёртывании ставьте перед шлюзом reverse proxy с ограничением запросов.
- **SQLite** — осознанный выбор: один инстанс шлюза, без горизонтального масштабирования.
- **Self-signed TLS** — клиентам нужен флаг `-k` / `--cacert` или установка сертификата в доверенные.
- **HS256 с общим секретом** — подходит для одного сервиса; секрет нужно хранить в тайне и периодически ротировать (ротация инвалидирует все выданные JWT).
- **Аудит fail-open** — см. раздел выше.
- **Нет refresh-токенов** — по замыслу, см. выше.
- Swagger UI включён по умолчанию; в production-конфигурации его следует отключить (`docs_url=None` в `app/main.py`).

## Стек

- Python 3.11+, FastAPI, uvicorn
- SQLAlchemy + SQLite, pydantic-settings (конфиг через `.env`)
- grpcio + сгенерированные стабы containerd API
- pyjwt, argon2-cffi
- pytest + httpx (TestClient)

## Быстрый старт

Самый быстрый путь — без containerd, на `FakeRuntime`.

### 1. Зависимости

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Конфигурация

```bash
cp .env.example .env
```

Для локального демо хватит значений по умолчанию (`DEBUG=true`, `RUNTIME_ADAPTER=fake`). Для любого другого запуска задайте секреты — см. [Конфигурация](#конфигурация).

### 3. TLS-сертификат

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=containerd-auth" \
  -addext "subjectAltName=DNS:containerd-auth,IP:127.0.0.1"
```

Если шлюз доступен по другому адресу (например, IP виртуальной машины), добавьте его в `subjectAltName`.

> `key.pem`, `cert.pem`, `.env` и `*.db` не должны попадать в git — они перечислены в `.gitignore`.

### 4. Запуск

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8443 \
  --ssl-certfile cert.pem --ssl-keyfile key.pem
```

Swagger UI: `https://<host>:8443/docs`

### 5. Проверка

```bash
curl -k -X POST https://localhost:8443/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<ADMIN_PASSWORD>"}'
```

## Конфигурация

Настройки читаются из `.env` (pydantic-settings). Шаблон — `.env.example`.

| Переменная          | По умолчанию                      | Описание                                                                                                 |
|---------------------|-----------------------------------|----------------------------------------------------------------------------------------------------------|
| `DEBUG`             | `true`                            | При `false` включается строгая валидация секретов (стандартные значения отклоняются при старте)          |
| `APP_DB_PATH`       | `app.db`                          | Путь к файлу SQLite (используется, если `APP_DB_URL` пуст)                                               |
| `APP_DB_URL`        | `—`                               | Полный URL, имеет приоритет над `APP_DB_PATH`. Postgresql: `postgresql+psycopg://user:pass@host:5432/db` | |
| `JWT_SECRET`        | `change-me`                       | Ключ подписи JWT (HS256). **Обязательно сменить** при `DEBUG=false`                                      |
| `JWT_TTL_MINUTES`   | `15`                              | Время жизни JWT в минутах                                                                                |
| `RUNTIME_ADAPTER`   | `fake`                            | `fake` — без containerd (демо/тесты), `containerd` — реальный рантайм                                    |
| `CONTAINERD_SOCKET` | `/run/containerd/containerd.sock` | Путь к unix-сокету containerd                                                                            |
| `ADMIN_USERNAME`    | `admin`                           | Логин администратора, создаваемого при старте                                                            |
| `ADMIN_PASSWORD`    | `change-me`                       | Пароль администратора. **Обязательно сменить** при `DEBUG=false`                                         |

Пример боевой конфигурации:

```bash
DEBUG=false
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_PASSWORD=<длинный случайный пароль>
RUNTIME_ADAPTER=containerd
```

## Настройка containerd

Нужна только при `RUNTIME_ADAPTER=containerd`. Идея: сокет containerd по умолчанию доступен только root, поэтому шлюз получает доступ через выделенную группу, а не через запуск от root.

### 1. Namespace

```bash
sudo ctr namespaces create containerd-auth
```

### 2. Группа и пользователь

```bash
sudo groupadd -r containerd
sudo usermod -aG containerd $USER
getent group containerd        # запомнить GID (третье поле)
```

После `usermod` нужно перелогиниться (или выполнить `newgrp containerd`), чтобы членство в группе вступило в силу.

### 3. Конфигурация containerd

```bash
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml > /dev/null
sudo nano /etc/containerd/config.toml
```

В секции gRPC укажите GID группы `containerd`:

```toml
[plugins."io.containerd.server.v1.grpc"]
  address = "/run/containerd/containerd.sock"
  uid = 0
  gid = <GID группы containerd>
```

### 4. Перезапуск и проверка

```bash
sudo systemctl restart containerd
ls -l /run/containerd/containerd.sock   # владелец root:containerd
```

Теперь шлюз можно запускать от обычного пользователя из группы `containerd`.

> ⚠️ Доступ к сокету containerd фактически равен root-доступу к хосту. Входите в группу `containerd` только тем учётным записям, которым это действительно нужно (в нашей схеме — сервисному пользователю шлюза).

## API

Аутентификация — `Authorization: Bearer <JWT>` либо `Bearer <API-токен>`. Роли: `—` (анонимно), `user`, `admin`. Чужой и несуществующий ресурс дают одинаковый 404.

| Метод  | Путь                      | Роль  | Назначение                                                        |
|--------|---------------------------|-------|-------------------------------------------------------------------|
| POST   | `/auth/login`             | —     | получить JWT по username/password                                 |
| PATCH  | `/auth/password`          | user  | сменить пароль (инвалидирует JWT и API-токены)                    |
| POST   | `/auth/tokens`            | user  | создать API-токен                                                 |
| DELETE | `/auth/tokens/{token_id}` | user  | отозвать свой API-токен                                           |
| POST   | `/images`                 | user  | pull образа из registry (например, docker.io/library/alpine:3.19) |
| GET    | `/images`                 | user  | список своих образов                                              |
| DELETE | `/images/{image_ref}`     | user  | удалить свой образ                                                |
| POST   | `/containers`             | user  | создать контейнер из своего образа                                |
| GET    | `/containers`             | user  | список своих контейнеров                                          |
| GET    | `/containers/{id}`        | user  | статус контейнера                                                 |
| POST   | `/containers/{id}/start`  | user  | запустить контейнер                                               |
| POST   | `/containers/{id}/stop`   | user  | остановить контейнер                                              |
| GET    | `/containers/{id}/logs`   | user  | логи контейнера                                                   |
| DELETE | `/containers/{id}`        | user  | удалить контейнер                                                 |
| GET    | `/admin/users`            | admin | список пользователей                                              |
| POST   | `/admin/users`            | admin | создать пользователя                                              |
| GET    | `/admin/users/{username}` | admin | профиль пользователя                                              |
| PATCH  | `/admin/users/{username}` | admin | изменить роль пользователя                                        |
| DELETE | `/admin/users/{username}` | admin | удалить пользователя                                              |
| GET    | `/admin/audit`            | admin | журнал аудита                                                     |

Коды ошибок:

| Код   | Значение                                          |
|-------|---------------------------------------------------|
| `401` | нет или невалидный токен                          |
| `403` | не хватает роли                                   |
| `404` | ресурс не существует или чужой (anti-enumeration) |
| `422` | невалидный ввод                                   |
| `502` | ошибка containerd / registry                      |

Полная интерактивная документация — Swagger UI (`/docs`) и `openapi.json`.

## Тестирование

```bash
pytest                          # unit + e2e через TestClient
python scripts/live_smoke.py    # smoke против живого шлюза
```

`scripts/demo.ps1` (PowerShell, Windows-хост) — сквозной сценарий: логин, лайфсайкл контейнеров, проверка матрицы 401/403/404, админ-операции, аудит.

## Тестирование безопасности

Проект прошёл цикл SAST → triage → fix → DAST → fix → re-scan.

**SAST** — bandit, semgrep (`p/owasp-top-ten`), pip-audit: критичных находок нет; находки bandit разобраны (false positive / intended / fixed). Отсутствие находок не гарантирует отсутствия уязвимостей.

**DAST** — OWASP ZAP:

- baseline scan (unauthenticated): 56 PASS, 5 WARN
- authenticated API-scan по `openapi.json` (bearer-токен): выявлен некорректный ответ 500 на pull несуществующего образа (gRPC-ошибка containerd не транслировалась) → введены доменные исключения в контракте `Runtime`, маппинг в 404/502 → re-scan чистый;
- authenticated API-scan по `openapi.json` (bearer-токен): выявлен некорректный ответ 500 на создание уже имеющегося контейнера, который создался в containerd, но БД не дошел → введены доменные исключения → re-scan чистый;
- re-scan: 120 PASS, 1 WARN
- целевые тесты (`demo.ps1`): матрица 401 (нет токена), 403 (vertical escalation), 404 (IDOR / anti-enumeration) — сценарии, недоступные слепому сканеру.

## Структура проекта

```
app/
  main.py            # приложение, security-headers middleware
  config.py          # pydantic-settings, валидация секретов
  db.py              # SQLAlchemy, модели (User, ImageOwnership, AuditLog, ...)
  rbac.py            # get_current_user, require_admin
  auth/              # аутентификация, токены
  routers/           # auth, containers, images, admin
  runtime/
    containerd_api/  # Сгенерированные gRPC стабы
    base.py          # ABC Runtime + доменные исключения
    fake.py          # in-memory реализация для демо/тестов
    containerd_runtime.py  # gRPC-адаптер containerd
    factory.py       # выбор адаптера по конфигу
tests/               # pytest: unit + e2e
scripts/             # demo.ps1, live_smoke.py
```

## Скриншоты

![Swagger UI](docs/screenshots/swagger.png) 

![demo.ps1](docs/screenshots/demo.png)

![ubuntu](docs/screenshots/containerd_ubuntu.png)

![log](docs/screenshots/log.png) |


## Лицензия

[The Unlicense](LICENSE)
