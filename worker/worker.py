"""
job-worker: читает задачи из Redis, исполняет их через API кластера 2,
записывает статус обратно в Redis.
"""
import json
import logging
import os
import shlex
import signal
import sys
import time
import uuid
from typing import Any

import httpx2
import redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("job-worker")

BASE_URL = os.getenv("WORKER_BASE_URL", "https://127.0.0.1:30443").rstrip("/")
API_TOKEN = os.getenv("WORKER_API_TOKEN")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
POLL_INTERVAL_SEC = int(os.getenv("WORKER_POLL_INTERVAL_SEC", "5"))
REQUEST_TIMEOUT_SEC = float(os.getenv("WORKER_REQUEST_TIMEOUT_SEC", "15.0"))
TLS_INSECURE = os.getenv("WORKER_TLS_INSECURE_SKIP_VERIFY", "true").lower() in ("true", "1", "yes")

QUEUE = "tasks"

if not API_TOKEN:
    logger.critical("FATAL: Environment variable API_TOKEN is not set! Worker cannot authenticate.")
    sys.exit(1)


class GracefulExit:
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logger.info("Received signal %s, exiting gracefully...", signum)
        self.kill_now = True


def get_redis_client(killer: GracefulExit) -> redis.Redis:
    """Подключение к Redis при старте пода."""
    retry_delay = 2
    while not killer.kill_now:
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True)
            r.ping()
            logger.info("Connected to Redis: %s", REDIS_URL)
            return r
        except Exception as e:
            logger.warning(
                "Waiting for Redis (%s): %s. Retry in %ds",
                REDIS_URL, e, retry_delay
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 10)
    sys.exit(0)


def wait_stopped(
    client: httpx2.Client,
    headers: dict[str, str],
    container_id: str,
    max_wait: float = 20.0
) -> None:
    """
    Опрос статуса контейнера до остановки.
    Демо-задачи короткие, макс 20с.
    """

    deadline = time.time() + max_wait
    delay = 1
    while time.time() < deadline:
        resp = client.get(f"/containers/{container_id}", headers=headers)
        if resp.status_code == 404:
            return
        resp.raise_for_status()
        state = (resp.json() or {}).get("status", "")
        if state == "stopped":
            return
        time.sleep(delay)
        delay = min(delay * 2, 4)
    logger.warning(
        "Container %s still not stopped after %.0fs, reading logs as-is",
        container_id, max_wait
    )


def execute_task(
    client: httpx2.Client,
    task: dict[str, Any]
) -> dict[str, Any]:
    """
    Выполняет задачу через API кластера 2 и возвращает результат.

    1. Пулл образа.
    2. Создание контейнера.
    3. Получение логов.
    4. Удаление контейнера.

    :param client: httpx2.Client для взаимодействия с API кластера 2
    :param task: Словарь с данными задачи, включая идентификатор и параметры
    :return: Словарь с результатом выполнения задачи, включая статус и логи
    :raises ValueError: Если задача не содержит обязательного поля 'id'
    """

    task_id = task.get("id")
    image = task.get("image", "docker.io/library/alpine:latest")
    base_command = task.get("command", "echo 'Task executed successfully!'")
    container_id = f"c-{task_id}"

    if isinstance(base_command, list):
        command_str = shlex.join(base_command)
    else:
        command_str = base_command

    if "/bin/sh" in command_str:
        command = base_command if isinstance(base_command, list) else [base_command]
    else:
        command = ["/bin/sh", "-c", command_str]

    if not task_id:
        raise ValueError("Task must have an 'id' field")

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    logger.info(
        "[%s] Starting task execution: image='%s', command=%s",
        task_id, image, command
    )
    start_time = time.time()
    container_created = False

    try:
        resp = client.post(
            "/images",
            json={"image_ref": image},
            headers=headers,
        )
        if resp.status_code in (200, 201):
            logger.info(
                "Image pulled successfully: %s",
                image
            )
        else:
            logger.warning(
                "Image pull %s -> %s %s",
                image, resp.status_code, resp.text[:200]
            )

        create_payload = {
            "container_id": container_id,
            "image": image,
            "command": command
        }
        resp = client.post(
            "/containers",
            json=create_payload,
            headers=headers,
        )
        resp.raise_for_status()
        container_created = True
        logger.info(
            "[%s] Container '%s' created.",
            task_id, container_id
        )

        wait_stopped(client=client, headers=headers, container_id=container_id)
        res_logs = client.get(f"/containers/{container_id}/logs", headers=headers)
        output = res_logs.text.strip() if res_logs.status_code == 200 else ""
        logger.info(
            "[%s] Execution output for '%s': %s",
            task_id, container_id, output[:500]
        )

        duration = round(time.time() - start_time, 2)
        return {
            "task_id": task_id,
            "status": "COMPLETED",
            "output": output,
            "duration": duration,
            "timestamp": int(time.time()),
        }

    finally:
        if container_created:
            try:
                client.delete(f"/containers/{container_id}", headers=headers)
                logger.info("[%s] Container cleaned up.", task_id)
            except Exception as e:
                logger.error(
                    "[%s] Cleanup failed for %s: %s",
                    task_id, container_id, e
                )


def process_task(
    r: redis.Redis,
    client: httpx2.Client,
    raw_task: str
) -> None:
    """
    Обрабатывает задачу, полученную из Redis.

    :param r: Redis клиент для взаимодействия с очередью задач
    :param client: httpx2.Client для взаимодействия с API кластера 2
    :param raw_task: Сырые данные задачи в формате JSON, полученные из Redis
    :return:
    """

    try:
        task: dict[str, Any] = json.loads(raw_task)
    except json.JSONDecodeError:
        logger.exception("Invalid JSON received: %s", raw_task)
        r.incr("metrics:tasks_failed")
        return

    task_id = task.get("id")
    if not task_id:
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        task["id"] = task_id
        logger.error(
            "Received task without 'id': %s. Generating automatically",
            task
        )

    logger.info("[%s] Processing task: %s", task_id, task)
    task_key = f"task:{task_id}"
    r.hset(
        task_key,
        mapping={"status": "IN_PROGRESS", "started_at": int(time.time())}
    )

    try:
        result = execute_task(client, task)

        if "timestamp" in result:
            result["finished_at"] = result.pop("timestamp")

        r.incr("metrics:tasks_completed")
        r.set("metrics:last_success_timestamp", int(time.time()))
        logger.info(
            "[%s] Task completed successfully.",
            task_id
        )
    except Exception as e:
        logger.error("[%s] Task failed: %s", task_id, e)
        result = {
            "task_id": task_id,
            "status": "FAILED",
            "error": str(e),
            "finished_at": int(time.time())
        }
        r.incr("metrics:tasks_failed")
        r.set("metrics:last_failed_timestamp", int(time.time()))

    r.hset(task_key, mapping=result)


def main():
    killer = GracefulExit()
    r = get_redis_client(killer)

    with httpx2.Client(
        base_url=BASE_URL,
        timeout=REQUEST_TIMEOUT_SEC,
        verify=not TLS_INSECURE,
    ) as client:
        logger.info(
            "Worker initialized. Target gateway: %s",
            BASE_URL
        )

        while not killer.kill_now:
            try:
                raw_task = r.blpop(QUEUE, timeout=POLL_INTERVAL_SEC)

                if not raw_task:
                    logger.debug("Queue empty for %ds", POLL_INTERVAL_SEC)
                    continue

                process_task(r, client, raw_task[1])

            except redis.RedisError as redis_err:
                logger.error(
                    "Redis connection error during polling: %s. Sleeping 2s...",
                    redis_err
                )
                time.sleep(2)

            except Exception as e:
                logger.exception(
                    "Unexpected system error in main loop: %s",
                    e
                )
                time.sleep(1)