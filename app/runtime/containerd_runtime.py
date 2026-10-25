import hashlib
import json
import threading
import platform
import time
import logging
from pathlib import Path

import grpc
from google.protobuf.any_pb2 import Any

from app.runtime.containerd_api import (
    ContainersStub,
    TasksStub,
    ImagesStub,
    TransferStub,
    CreateContainerRequest,
    Container,
    SnapshotsStub,
    PrepareSnapshotRequest,
    CreateTaskRequest,
    StartRequest,
    DeleteTaskRequest,
    KillRequest,
    DeleteContainerRequest,
    RemoveSnapshotRequest,
    ListContainersRequest,
    ListTasksRequest,
    GetContainerRequest,
    OCIRegistry,
    ImageStore,
    RegistryResolver,
    UnpackConfiguration,
    TransferRequest,
    ListImagesRequest,
    DeleteImageRequest,
    GetImageRequest,
    ReadContentRequest,
    ContentStub,
    WaitRequest,
    MountsRequest,
    StatSnapshotRequest
)
from app.runtime.base import Runtime, RuntimeNotFound, RuntimeUnavailable, RuntimeConflict

logger = logging.getLogger(__name__)

_TURL_REG = "containerd.types.transfer.OCIRegistry"
_TURL_IMG = "containerd.types.transfer.ImageStore"

_SIGKILL = 9
_STATUS_MAP = {
    0: "unknown",
    1: "created",
    2: "running",
    3: "stopped",
    4: "stopped",
    "UNKNOWN": "unknown",
    "CREATED": "created",
    "RUNNING": "running",
    "STOPPED": "stopped",
    "PAUSED": "stopped",
}


class ContainerdRuntime(Runtime):
    def __init__(
        self,
        socket: str = "unix:///run/containerd/containerd.sock",
        namespace: str = "containerd-auth",
        log_dir: str = "logs",
    ):
        self._channel = grpc.insecure_channel(socket)
        self._namespace = namespace
        self._ns = ("containerd-namespace", namespace)
        self._log_dir = Path(log_dir).resolve()
        self._log_locks: dict[str, threading.Lock] = {}
        self._mounts_by_cid: dict[str, list] = {}
        self._log_locks_guard = threading.Lock()

        self._containers = ContainersStub(self._channel)
        self._tasks = TasksStub(self._channel)
        self._images = ImagesStub(self._channel)
        self._transfer = TransferStub(self._channel)
        self._content = ContentStub(self._channel)
        self._snapshots = SnapshotsStub(self._channel)

        self._log_dir.mkdir(parents=True, exist_ok=True)

    # === Helpers ===

    def _metadata(self, *args):
        return (*args, self._ns) if args else (self._ns,)

    def _log_file(self, container_id: str) -> Path:
        return self._log_dir / f"{container_id}.log"

    def _log_lock(self, container_id: str) -> threading.Lock:
        with self._log_locks_guard:
            return self._log_locks.setdefault(container_id, threading.Lock())

    def _get_mounts(self, container_id: str) -> list:
        resp = self._snapshots.Mounts(
            MountsRequest(key=container_id, snapshotter="overlayfs"),
            metadata=self._metadata()
        )
        return list(resp.mounts)

    def _prepare_snapshot(self, container_id: str, image: str) -> None:
        parent = self._get_snapshot_parent(image)
        prep = self._snapshots.Prepare(
            PrepareSnapshotRequest(
                key=container_id,
                parent=parent,
                snapshotter="overlayfs"
            ),
            metadata=self._metadata(),
        )
        self._mounts = list(prep.mounts)
        self._mounts_by_cid[container_id] = self._mounts

    def _get_snapshot_parent(self, ref: str) -> str:
        try:
            img = self._images.Get(
                GetImageRequest(name=ref),
                metadata=self._metadata()
            ).image
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise RuntimeNotFound(f"image {ref!r} not found") from e
            raise

        def blob(digest: str) -> bytes:
            resp = self._content.Read(
                ReadContentRequest(digest=digest),
                metadata=self._metadata()
            )
            return b"".join(chunk.data for chunk in resp)

        data = json.loads(blob(img.target.digest))

        if "manifests" in data and "config" not in data:
            arch = platform.machine()
            if arch == "x86_64":
                arch = "amd64"

            target_manifest_digest = None
            for manifest_descriptor in data["manifests"]:
                p = manifest_descriptor.get("platform", {})
                if p.get("architecture") == arch and p.get("os") == "linux":
                    target_manifest_digest = manifest_descriptor["digest"]
                    break

            if not target_manifest_digest:
                target_manifest_digest = next(
                    (m["digest"] for m in data["manifests"] if m.get("platform", {}).get("os") == "linux"),
                    None
                )

            if not target_manifest_digest:
                raise RuntimeError(f"No suitable manifest found for architecture {arch} in image {ref}")

            manifest = json.loads(blob(target_manifest_digest))
        else:
            manifest = data

        config = json.loads(blob(manifest["config"]["digest"]))
        diff_ids: list[str] = config["rootfs"]["diff_ids"]

        chain = diff_ids[0]
        for diff in diff_ids[1:]:
            chain = "sha256:" + hashlib.sha256(f"{chain} {diff}".encode()).hexdigest()
        return chain

    def _create_task(self, container_id: str) -> None:
        try:
            self._tasks.Delete(
                DeleteTaskRequest(container_id=container_id),
                metadata=self._metadata()
            )
        except grpc.RpcError:
            pass

        logfile = self._log_file(container_id)
        with self._log_lock(container_id):
            logfile.write_bytes(b"")

        mounts = self._get_mounts(container_id)

        self._tasks.Create(
            CreateTaskRequest(
                container_id=container_id,
                rootfs=mounts,
                stdout=logfile.as_posix(),
                stderr=logfile.as_posix(),
            ),
            metadata=self._metadata(),
        )
        self._tasks.Start(StartRequest(container_id=container_id), metadata=self._metadata())

    def _task_status(self, container_id: str) -> str:
        try:
            resp = self._tasks.List(
                ListTasksRequest(),
                metadata=self._metadata()
            )
        except grpc.RpcError:
            return "unknown"

        for t in resp.tasks:
            if t.id == container_id:
                return _STATUS_MAP.get(t.status, str(t.status).lower())
        return "created"

    def _wait_for_snapshot(
        self,
        chain_id: str,
        snapshotter: str = "overlayfs",
        timeout: float = 30,
    ) -> None:
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                self._snapshots.Stat(
                    StatSnapshotRequest(key=chain_id, snapshotter=snapshotter),
                    metadata=self._metadata()
                )
                return
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    time.sleep(0.2)
                    continue
                raise

        raise TimeoutError(f"Snapshot {chain_id} not found after {timeout} seconds")

    @staticmethod
    def _translate_transfer_error(err: grpc.RpcError, image: str) -> None:
        """Маппинг gRPC-ошибок Transfer в domain-исключения контракта Runtime."""
        code = err.code()
        details = err.details() or ""
        not_found_markers = (
            "failed to resolve image",
            "object required",
            "not found",
            "does not exist",
        )
        if code == grpc.StatusCode.NOT_FOUND or any(
                m in details.lower() for m in not_found_markers
        ):
            raise RuntimeNotFound(f"image {image!r} not found in registry") from err
        raise RuntimeUnavailable(f"transfer failed: {code.name}: {details}") from err

    # === Images ===

    def pull_image(self, image: str) -> None:
        src = OCIRegistry(
            reference=image,
            resolver=RegistryResolver(default_scheme="https"),
        )
        dst = ImageStore(
            name=image,
            unpacks=[UnpackConfiguration(snapshotter="overlayfs")],
        )

        def pack(msg, type_url: str):
            any_msg = Any()
            any_msg.type_url = type_url
            any_msg.value = msg.SerializeToString()
            return any_msg

        req = TransferRequest(
            source=pack(src, _TURL_REG),
            destination=pack(dst, _TURL_IMG),
        )
        try:
            self._transfer.Transfer(req, metadata=self._metadata(), timeout=600)
        except grpc.RpcError as e:
            self._translate_transfer_error(e, image)

        parent = self._get_snapshot_parent(image)
        self._wait_for_snapshot(parent)

    def list_images(self) -> list[dict]:
        resp = self._images.List(
            ListImagesRequest(),
            metadata=self._metadata()
        )
        return [img.name for img in resp.images]

    def remove_image(self, image: str) -> None:
        try:
            self._images.Delete(
                DeleteImageRequest(name=image),
                metadata=self._metadata()
            )
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.NOT_FOUND:
                raise

    # === Containers ===

    def create_container(
        self,
        container_id: str,
        image: str,
        command: list[str] | None = None
    ) -> str:
        """
        Создает и запускает контейнер.

        spec — это JSON-описание контейнера в формате OCI Runtime Spec.
            Если command не указан, используется дефолтный
            `echo hello; sleep 300`, чтобы контейнер оставался
            запущенным для демонстрации.

        :param container_id: имя контейнера (id)
        :param image: имя образа
        :param command: argv процесса внутри контейнера, например,
            ["/bin/sh", "-c", "echo hello; sleep 300"] или
            ["nginx", "-g", "daemon off;"]

        :return: id созданного контейнера
        """
        args = command or ["/bin/sh", "-c", "echo hello; sleep 300"]
        spec_json = json.dumps({
            "ociVersion": "1.0",
            "process": {
                "args": args,
                "terminal": False,
                "user": {"uid": 0, "gid": 0},
                "env": [
                    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                    "TERM=xterm",
                ],
                "cwd": "/"
            },
            "root": {
                "path": "rootfs",
                "readonly": False
            },
            "mounts": [
                {
                    "destination": "/proc",
                    "type": "proc",
                    "source": "proc"
                },
                {
                    "destination": "/dev",
                    "type": "tmpfs",
                    "source": "tmpfs",
                    "options": ["nosuid", "strictatime", "mode=755", "size=65536k"]
                },
                {
                    "destination": "/dev/pts",
                    "type": "devpts",
                    "source": "devpts",
                    "options": ["nosuid", "noexec", "newinstance", "ptmxmode=0666", "mode=0620", "gid=5"]
                },
                {
                    "destination": "/dev/shm",
                    "type": "tmpfs",
                    "source": "shm",
                    "options": ["nosuid", "noexec", "nodev", "mode=1777", "size=65536k"]
                },
                {
                    "destination": "/sys",
                    "type": "sysfs",
                    "source": "sysfs",
                    "options": ["nosuid", "noexec", "nodev", "ro"]
                }
            ],
            "linux": {
                "namespaces": [
                    {"type": "pid"},
                    {"type": "network"},
                    {"type": "ipc"},
                    {"type": "uts"},
                    {"type": "mount"}
                ]
            }
        }).encode()
        spec_any = Any(
            type_url="types.containerd.io/opencontainers/runtime-spec/1/Spec",
            value=spec_json
        )

        try:
            self._containers.Create(
                CreateContainerRequest(
                    container=Container(
                        id=container_id,
                        image=image,
                        runtime=Container.Runtime(name="io.containerd.runc.v2"),
                        spec=spec_any,
                        snapshotter="overlayfs",
                        snapshot_key=container_id
                    ),
                ),
                metadata=self._metadata(),
            )
        except grpc.RpcError as e:
            code = e.code()
            if code == grpc.StatusCode.ALREADY_EXISTS:
                raise RuntimeConflict(f"container {container_id!r} already exists") from e
            raise RuntimeUnavailable(f"{code.name}: container creation failed") from e

        try:
            self._prepare_snapshot(container_id, image)
            self._create_task(container_id)
        except Exception as e:
            try:
                self._containers.Delete(
                    DeleteContainerRequest(id=container_id),
                    metadata=self._metadata()
                )
            except Exception:
                logger.exception("rollback: failed to delete container %r", container_id)
            raise RuntimeUnavailable(f"container creation failed: {e}") from e
        return container_id

    def start(self, container_id: str) -> None:
        status = self._task_status(container_id)

        if status == "running":
            return

        if status in ("created", "stopped"):
            self._create_task(container_id)
            return

        self._tasks.Start(StartRequest(container_id=container_id), metadata=self._metadata())

    def stop(self, container_id: str) -> None:
        try:
            self._tasks.Kill(
                KillRequest(container_id=container_id, signal=_SIGKILL),
                metadata=self._metadata()
            )
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return
            raise

        try:
            self._tasks.Wait(
                WaitRequest(container_id=container_id),
                metadata=self._metadata()
            )
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.NOT_FOUND:
                raise

    def remove(self, container_id: str) -> None:
        self.stop(container_id)

        try:
            self._tasks.Delete(
                DeleteTaskRequest(container_id=container_id),
                metadata=self._metadata()
            )
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.NOT_FOUND:
                raise

        self._containers.Delete(
            DeleteContainerRequest(id=container_id),
            metadata=self._metadata()
        )

        self._mounts_by_cid.pop(container_id, None)

        try:
            self._snapshots.Remove(
                RemoveSnapshotRequest(key=container_id, snapshotter="overlayfs"),
                metadata=self._metadata()
            )
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.NOT_FOUND:
                raise

        with self._log_lock(container_id):
            self._log_file(container_id).unlink(missing_ok=True)

    def logs(self, container_id: str, tail: int = 200) -> str:
        f = self._log_file(container_id)
        if not f.exists():
            return ""
        lines = f.read_text(errors="replace").splitlines()
        return "\n".join(lines[-tail:])

    def list_containers(self) -> list[dict]:
        resp = self._containers.List(
            ListContainersRequest(),
            metadata=self._metadata()
        )
        return [
            {
                "id": c.id,
                "image": c.image,
                "status": self._task_status(c.id)
            } for c in resp.containers
        ]

    def get_container(self, container_id: str) -> dict:
        c = self._containers.Get(
            GetContainerRequest(id=container_id),
            metadata=self._metadata()
        ).container
        return {
            "id": c.id,
            "image": c.image,
            "status": self._task_status(container_id)
        }
