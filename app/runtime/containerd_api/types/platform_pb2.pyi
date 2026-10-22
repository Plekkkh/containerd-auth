from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Platform(_message.Message):
    __slots__ = ("os", "architecture", "variant", "os_version", "os_features")
    OS_FIELD_NUMBER: _ClassVar[int]
    ARCHITECTURE_FIELD_NUMBER: _ClassVar[int]
    VARIANT_FIELD_NUMBER: _ClassVar[int]
    OS_VERSION_FIELD_NUMBER: _ClassVar[int]
    OS_FEATURES_FIELD_NUMBER: _ClassVar[int]
    os: str
    architecture: str
    variant: str
    os_version: str
    os_features: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, os: _Optional[str] = ..., architecture: _Optional[str] = ..., variant: _Optional[str] = ..., os_version: _Optional[str] = ..., os_features: _Optional[_Iterable[str]] = ...) -> None: ...
