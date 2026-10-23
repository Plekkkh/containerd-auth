from abc import ABC, abstractmethod


class RuntimeNotFound(Exception):
    """Запрошенный объект не существует у registry/runtime."""


class RuntimeUnavailable(Exception):
    """Runtime/registry недоступен или вернул неустранимую ошибку."""


class RuntimeConflict(Exception):
    """Ресурс с таким идентификатором уже существует."""


class Runtime(ABC):
    @abstractmethod
    def create_container(
        self,
        container_id: str,
        image: str,
        command: list[str] | None = None,
    ) -> str:
        ...

    @abstractmethod
    def start(self, container_id: str) -> None: ...
    
    @abstractmethod
    def stop(self, container_id: str) -> None: ...

    @abstractmethod
    def remove(self, container_id: str) -> None: ...

    @abstractmethod
    def logs(self, container_id: str, tail: int = 200) -> str: ...

    @abstractmethod
    def list_containers(self) -> list[dict]: ...

    @abstractmethod
    def get_container(self, container_id: str) -> dict: ...

    @abstractmethod
    def pull_image(self, image: str) -> None: ...

    @abstractmethod
    def list_images(self) -> list[dict]: ...

    @abstractmethod
    def remove_image(self, image: str) -> None: ...
