import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Mount(_message.Message):
    __slots__ = ("type", "source", "target", "options")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    type: str
    source: str
    target: str
    options: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, type: _Optional[str] = ..., source: _Optional[str] = ..., target: _Optional[str] = ..., options: _Optional[_Iterable[str]] = ...) -> None: ...

class ActiveMount(_message.Message):
    __slots__ = ("mount", "mounted_at", "mount_point", "data")
    class DataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    MOUNT_FIELD_NUMBER: _ClassVar[int]
    MOUNTED_AT_FIELD_NUMBER: _ClassVar[int]
    MOUNT_POINT_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    mount: Mount
    mounted_at: _timestamp_pb2.Timestamp
    mount_point: str
    data: _containers.ScalarMap[str, str]
    def __init__(self, mount: _Optional[_Union[Mount, _Mapping]] = ..., mounted_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., mount_point: _Optional[str] = ..., data: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ActivationInfo(_message.Message):
    __slots__ = ("name", "active", "system", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    active: _containers.RepeatedCompositeFieldContainer[ActiveMount]
    system: _containers.RepeatedCompositeFieldContainer[Mount]
    labels: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., active: _Optional[_Iterable[_Union[ActiveMount, _Mapping]]] = ..., system: _Optional[_Iterable[_Union[Mount, _Mapping]]] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class MountCapabilities(_message.Message):
    __slots__ = ("types", "transforms")
    TYPES_FIELD_NUMBER: _ClassVar[int]
    TRANSFORMS_FIELD_NUMBER: _ClassVar[int]
    types: _containers.RepeatedScalarFieldContainer[str]
    transforms: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, types: _Optional[_Iterable[str]] = ..., transforms: _Optional[_Iterable[str]] = ...) -> None: ...
