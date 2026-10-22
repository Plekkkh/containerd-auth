from app.runtime.base import Runtime

class FakeRuntime(Runtime):
    def __init__(self):
        self._containers: dict[str, dict] = {}
        self._images: set[str] = set()

    def create_container(self, container_id: str, image: str) -> str:
        container_id = container_id
        self._containers[container_id] = {
            "id": container_id,
            "name": container_id,
            "image": image,
            "is_running": False,
        }
        return container_id

    def start(self, container_id: str) -> None:
        self._containers[container_id]["is_running"] = True

    def stop(self, container_id: str) -> None:
        self._containers[container_id]["is_running"] = False

    def remove(self, container_id: str) -> None:
        del self._containers[container_id]

    def logs(self, container_id: str) -> str:
        return f"[fake] Logs for container {container_id}\n"

    def list_containers(self) -> list[dict]:
        return list(self._containers.values())

    def get_container(self, container_id: str) -> dict:
        return self._containers[container_id]

    def pull_image(self, image: str) -> None:
        self._images.add(image)

    def list_images(self) -> list[dict]:
        return [{"name": image} for image in sorted(self._images)]

    def remove_image(self, image: str) -> None:
        self._images.discard(image)