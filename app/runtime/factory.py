from app.config import Settings
from app.runtime.base import Runtime
from app.runtime.fake import FakeRuntime


def make_runtime(settings: Settings) -> Runtime:
    match settings.RUNTIME_ADAPTER:
        case "fake":
            return FakeRuntime()
        case "containerd":
            from app.runtime.containerd_runtime import ContainerdRuntime

            sock = settings.CONTAINERD_SOCKET
            if "://" not in sock:
                sock = f"unix://{sock}"
            return ContainerdRuntime(sock, log_dir=settings.LOG_DIR)
        case _:
            raise ValueError(f"Unknown runtime adapter: {settings.RUNTIME_ADAPTER}")
