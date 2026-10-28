#!/usr/bin/env python3
"""
demo-dispatch: генератор демо-задач для job-worker.

Кладёт задачи в Redis-очередь 'tasks' (RPUSH — воркер делает BLPOP,
таким образом сохраняется FIFO). Ничего не исполняет сам и не ходит
в API кластера 2 — только наполняет очередь.

Контракт задачи (ветка deploy, worker/worker.py):
    {"id": str, "image": str, "command": list[str]}

Два режима доставки в Redis:
  * --k8s (по умолчанию): kubectl exec в под redis и redis-cli RPUSH.
    Port-forward не нужен, NetworkPolicy (ingress только от job-worker)
    не ослабляется — exec идёт через kubelet API, а не через сетевые
    правила пода.
  * --direct: прямое подключение по REDIS_URL. Нужно, если у тебя
    поднят port-forward или Redis реально торчит наружу. Требует
    pip install redis.

Запуск:
    python3 demo-dispatch.py                        # стандартный набор, k8s-режим
    python3 demo-dispatch.py --preset standard -n 3
    python3 demo-dispatch.py --task-file my-tasks.json
    python3 demo-dispatch.py --direct --redis-url redis://127.0.0.1:6379/0

Статусы смотреть в Redis: HGETALL task:{id}, счётчики metrics:tasks_completed|failed.
"""
import argparse
import json
import os
import subprocess
import sys
import uuid

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE = "tasks"

# Параметры k8s-режима (можно переопределить через env).
KUBE_CONTEXT = os.getenv("KUBE_CONTEXT", "kind-containerd-auth-client")
KUBE_NAMESPACE = os.getenv("KUBE_NAMESPACE", "client")
REDIS_POD_LABEL = "app=redis"

# Готовые наборы задач для показа преподавателю.
# command — список строк; воркер обернёт его в ['/bin/sh', '-c', ...].
PRESETS: dict[str, list[dict]] = {
    # Базовое демо: короткие команды, заметный вывод.
    "standard": [
        {
            "id": "demo-echo",
            "image": "docker.io/library/alpine:latest",
            "command": ["echo", "Worker task executed successfully!"],
        },
        {
            "id": "demo-issue",
            "image": "docker.io/library/alpine:latest",
            "command": ["sha256sum", "/etc/issue"],
        },
        {
            "id": "demo-uname",
            "image": "docker.io/library/alpine:latest",
            "command": ["uname", "-a"],
        },
    ],
    # Долгий таск — удобно показывать wait_stopped и очистку контейнера.
    "long": [
        {
            "id": "demo-long",
            "image": "docker.io/library/alpine:latest",
            "command": ["sleep", "8", "&&", "echo", "long task done"],
        },
    ],
    # Провокация отказа (образ не существует — воркер упадёт в FAILED).
    "failure": [
        {
            "id": "demo-fail-image",
            "image": "docker.io/library/busybox:1.36-nonexistent",
            "command": ["echo", "never runs"],
        },
    ],
}
PRESETS["mixed"] = PRESETS["standard"] + PRESETS["long"]


def build_tasks(args: argparse.Namespace) -> list[dict]:
    if args.task_file:
        with open(args.task_file, encoding="utf-8") as f:
            tasks = json.load(f)
        if not isinstance(tasks, list):
            raise SystemExit("task-file must contain a JSON array of tasks")
        return tasks

    preset = PRESETS.get(args.preset)
    if preset is None:
        raise SystemExit(f"Unknown preset '{args.preset}'. Available: {', '.join(PRESETS)}")

    tasks: list[dict] = []
    for i in range(args.count):
        base = dict(preset[i % len(preset)])
        # Уникальные id при повторе, чтобы hash task:{id} не перезатирался.
        if args.count > len(preset):
            base["id"] = f"{base['id']}-{uuid.uuid4().hex[:6]}"
        tasks.append(base)
    return tasks


# ---------- Режим 1: kubectl exec (по умолчанию) ----------

def _kubectl(*args: str, stdin: str | None = None) -> str:
    r = subprocess.run(
        ["kubectl", "--context", KUBE_CONTEXT, "-n", KUBE_NAMESPACE, *args],
        capture_output=True, text=True, input=stdin,
    )
    if r.returncode != 0:
        raise SystemExit(f"kubectl failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout


def redis_pod_name() -> str:
    out = _kubectl("get", "pods", "-l", REDIS_POD_LABEL,
                   "-o", "jsonpath={.items[0].metadata.name}")
    if not out:
        raise SystemExit("Redis pod not found (label app=redis). Deployed?")
    return out


# Кэш имени пода, чтобы не дергать get pods на каждую задачу.
_POD_NAME: str | None = None


def redis_cli(*args: str, stdin: str | None = None) -> str:
    global _POD_NAME
    if _POD_NAME is None:
        _POD_NAME = redis_pod_name()
    return _kubectl("exec", "-i", _POD_NAME, "--", "redis-cli", *args, stdin=stdin)


# ---------- Режим 2: прямой redis-py ----------

def push_task(task: dict, use_k8s: bool, redis_url: str) -> None:
    payload = json.dumps(task)
    if use_k8s:
        redis_cli("-x", "RPUSH", QUEUE, stdin=payload)
    else:
        import redis  # lazy: k8s-режиму этот пакет не нужен
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
        r.rpush(QUEUE, payload)


def queue_len(use_k8s: bool, redis_url: str) -> int:
    if use_k8s:
        return int(redis_cli("LLEN", QUEUE).strip())
    import redis  # lazy
    return redis.from_url(redis_url).llen(QUEUE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Push demo tasks into the job-worker queue.")
    parser.add_argument("--preset", default="standard", choices=sorted(PRESETS),
                        help="Набор демо-задач (default: standard)")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="Сколько всего задач создать (пресет циклически)")
    parser.add_argument("--image", help="Переопределить образ во всех задачах")
    parser.add_argument("--task-file", help="JSON-файл с массивом своих задач")
    parser.add_argument("--k8s", action="store_true", default=True,
                        help="Ходить через kubectl exec в redis (default)")
    parser.add_argument("--direct", dest="k8s", action="store_false",
                        help="Прямое подключение по REDIS_URL (нужен pip install redis)")
    parser.add_argument("--redis-url", default=REDIS_URL,
                        help="Redis URL для --direct (default: %(default)s)")
    args = parser.parse_args()

    tasks = build_tasks(args)
    if args.image:
        for t in tasks:
            t["image"] = args.image

    mode = "kubectl exec" if args.k8s else "direct"
    print(f"Dispatching {len(tasks)} task(s) to '{QUEUE}' (mode: {mode}):")
    for t in tasks:
        push_task(t, args.k8s, args.redis_url)
        print(f"  -> {t['id']}: image={t.get('image')}, command={t.get('command')}")

    print(f"Done. Queue length now: {queue_len(args.k8s, args.redis_url)}. "
          f"Worker status in hashes task:{{id}}.")


if __name__ == "__main__":
    sys.exit(main())
