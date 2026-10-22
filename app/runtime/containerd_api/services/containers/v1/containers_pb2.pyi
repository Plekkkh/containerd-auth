import datetime

from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import field_mask_pb2 as _field_mask_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Container(_message.Message):
    __slots__ = ("id", "labels", "image", "runtime", "spec", "snapshotter", "snapshot_key", "created_at", "updated_at", "extensions", "sandbox")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class Runtime(_message.Message):
        __slots__ = ("name", "options")
        NAME_FIELD_NUMBER: _ClassVar[int]
        OPTIONS_FIELD_NUMBER: _ClassVar[int]
        name: str
        options: _any_pb2.Any
        def __init__(self, name: _Optional[str] = ..., options: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
    class ExtensionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _any_pb2.Any
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_FIELD_NUMBER: _ClassVar[int]
    SPEC_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_KEY_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXTENSIONS_FIELD_NUMBER: _ClassVar[int]
    SANDBOX_FIELD_NUMBER: _ClassVar[int]
    id: str
    labels: _containers.ScalarMap[str, str]
    image: str
    runtime: Container.Runtime
    spec: _any_pb2.Any
    snapshotter: str
    snapshot_key: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    extensions: _containers.MessageMap[str, _any_pb2.Any]
    sandbox: str
    def __init__(self, id: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ..., image: _Optional[str] = ..., runtime: _Optional[_Union[Container.Runtime, _Mapping]] = ..., spec: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., snapshotter: _Optional[str] = ..., snapshot_key: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., extensions: _Optional[_Mapping[str, _any_pb2.Any]] = ..., sandbox: _Optional[str] = ...) -> None: ...

class GetContainerRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetContainerResponse(_message.Message):
    __slots__ = ("container",)
    CONTAINER_FIELD_NUMBER: _ClassVar[int]
    container: Container
    def __init__(self, container: _Optional[_Union[Container, _Mapping]] = ...) -> None: ...

class ListContainersRequest(_message.Message):
    __slots__ = ("filters",)
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    filters: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, filters: _Optional[_Iterable[str]] = ...) -> None: ...

class ListContainersResponse(_message.Message):
    __slots__ = ("containers",)
    CONTAINERS_FIELD_NUMBER: _ClassVar[int]
    containers: _containers.RepeatedCompositeFieldContainer[Container]
    def __init__(self, containers: _Optional[_Iterable[_Union[Container, _Mapping]]] = ...) -> None: ...

class CreateContainerRequest(_message.Message):
    __slots__ = ("container",)
    CONTAINER_FIELD_NUMBER: _ClassVar[int]
    container: Container
    def __init__(self, container: _Optional[_Union[Container, _Mapping]] = ...) -> None: ...

class CreateContainerResponse(_message.Message):
    __slots__ = ("container",)
    CONTAINER_FIELD_NUMBER: _ClassVar[int]
    container: Container
    def __init__(self, container: _Optional[_Union[Container, _Mapping]] = ...) -> None: ...

class UpdateContainerRequest(_message.Message):
    __slots__ = ("container", "update_mask")
    CONTAINER_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    container: Container
    update_mask: _field_mask_pb2.FieldMask
    def __init__(self, container: _Optional[_Union[Container, _Mapping]] = ..., update_mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ...) -> None: ...

class UpdateContainerResponse(_message.Message):
    __slots__ = ("container",)
    CONTAINER_FIELD_NUMBER: _ClassVar[int]
    container: Container
    def __init__(self, container: _Optional[_Union[Container, _Mapping]] = ...) -> None: ...

class DeleteContainerRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ListContainerMessage(_message.Message):
    __slots__ = ("container",)
    CONTAINER_FIELD_NUMBER: _ClassVar[int]
    container: Container
    def __init__(self, container: _Optional[_Union[Container, _Mapping]] = ...) -> None: ...
