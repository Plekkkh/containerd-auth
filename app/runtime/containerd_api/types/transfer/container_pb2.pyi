from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ContainerPath(_message.Message):
    __slots__ = ("container_id", "path", "no_walk", "preserve_ownership")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    NO_WALK_FIELD_NUMBER: _ClassVar[int]
    PRESERVE_OWNERSHIP_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    path: str
    no_walk: bool
    preserve_ownership: bool
    def __init__(self, container_id: _Optional[str] = ..., path: _Optional[str] = ..., no_walk: _Optional[bool] = ..., preserve_ownership: _Optional[bool] = ...) -> None: ...
