"""
Запуск (venv, из корня проекта):
    python -m scripts.live_smoke
Ожидаемая последовательность: version ok -> pull alpine -> images ls ->
create -> get/list -> start -> logs -> stop -> remove -> images ls (alpine нет).

Каждый шаг печатает [OK]/[FAIL]; при FAIL — трейсбек и стоп.
"""
from __future__ import annotations

import sys
import time
import traceback

sys.path.insert(0, ".")

from app.runtime.containerd_runtime import ContainerdRuntime

REF = "docker.io/library/alpine:3.19"
NAME = "smoke-1"


def step(label: str, fn):
    print(f"[*] {label} ...", flush=True)
    t0 = time.monotonic()
    try:
        result = fn()
    except Exception:
        print(f"[FAIL] {label} ({time.monotonic() - t0:.1f}s)")
        traceback.print_exc()
        sys.exit(1)
    print(f"[OK] {label} ({time.monotonic() - t0:.1f}s) -> {result!r}"[:300])
    return result


def main() -> None:
    rt = ContainerdRuntime()

    step("handshake: list_containers", lambda: rt.list_containers())
    step("cleanup: remove stale smoke container", lambda: rt.remove(NAME) and None
         if NAME in [c["id"] for c in rt.list_containers()] else "absent")

    step(f"pull {REF}", lambda: rt.pull_image(REF))
    images = step("list_images", rt.list_images)
    assert REF in images, f"{REF} not in image list: {images}"

    cid = step(f"create_container({NAME})", lambda: rt.create_container(NAME, REF))
    got = step("get_container", lambda: rt.get_container(cid))
    assert got["id"] == cid, got
    lst = step("list_containers", rt.list_containers)
    assert any(c["id"] == cid for c in lst), lst

    step("start", lambda: rt.start(cid))
    time.sleep(1.0)
    got = step("get_container after start", lambda: rt.get_container(cid))
    print(f"    status after start: {got['status']}")
    assert got["status"] == "running", got

    time.sleep(1.0)
    logs = step("logs", lambda: rt.logs(cid))
    print(f"    logs ({len(logs)} bytes): {logs[:120]!r}")

    step("stop", lambda: rt.stop(cid))
    got = step("get_container after stop", lambda: rt.get_container(cid))
    print(f"    status after stop: {got['status']}")
    assert got["status"] == "stopped", got

    step("restart: start after stop", lambda: rt.start(cid))
    time.sleep(1.0)
    got = step("get_container after restart", lambda: rt.get_container(cid))
    print(f"    status after restart: {got['status']}")
    assert got["status"] == "running", got

    step("stop again before remove", lambda: rt.stop(cid))

    step("remove container", lambda: rt.remove(cid))
    lst = step("list_containers after remove", rt.list_containers)
    assert not any(c["id"] == cid for c in lst), lst

    step(f"remove_image {REF}", lambda: rt.remove_image(REF))
    images = step("list_images after remove", rt.list_images)
    assert REF not in images, images

    print("\nALL SMOKE STEPS PASSED")


if __name__ == "__main__":
    main()
