import datetime

from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import field_mask_pb2 as _field_mask_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from types import mount_pb2 as _mount_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Kind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[Kind]
    VIEW: _ClassVar[Kind]
    ACTIVE: _ClassVar[Kind]
    COMMITTED: _ClassVar[Kind]
UNKNOWN: Kind
VIEW: Kind
ACTIVE: Kind
COMMITTED: Kind

class PrepareSnapshotRequest(_message.Message):
    __slots__ = ("snapshotter", "key", "parent", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    PARENT_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    key: str
    parent: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, snapshotter: _Optional[str] = ..., key: _Optional[str] = ..., parent: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class PrepareSnapshotResponse(_message.Message):
    __slots__ = ("mounts",)
    MOUNTS_FIELD_NUMBER: _ClassVar[int]
    mounts: _containers.RepeatedCompositeFieldContainer[_mount_pb2.Mount]
    def __init__(self, mounts: _Optional[_Iterable[_Union[_mount_pb2.Mount, _Mapping]]] = ...) -> None: ...

class ViewSnapshotRequest(_message.Message):
    __slots__ = ("snapshotter", "key", "parent", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    PARENT_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    key: str
    parent: str
    labels: _containers.ScalarMap[str, str]
    def __init__(self, snapshotter: _Optional[str] = ..., key: _Optional[str] = ..., parent: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ViewSnapshotResponse(_message.Message):
    __slots__ = ("mounts",)
    MOUNTS_FIELD_NUMBER: _ClassVar[int]
    mounts: _containers.RepeatedCompositeFieldContainer[_mount_pb2.Mount]
    def __init__(self, mounts: _Optional[_Iterable[_Union[_mount_pb2.Mount, _Mapping]]] = ...) -> None: ...

class MountsRequest(_message.Message):
    __slots__ = ("snapshotter", "key")
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    key: str
    def __init__(self, snapshotter: _Optional[str] = ..., key: _Optional[str] = ...) -> None: ...

class MountsResponse(_message.Message):
    __slots__ = ("mounts",)
    MOUNTS_FIELD_NUMBER: _ClassVar[int]
    mounts: _containers.RepeatedCompositeFieldContainer[_mount_pb2.Mount]
    def __init__(self, mounts: _Optional[_Iterable[_Union[_mount_pb2.Mount, _Mapping]]] = ...) -> None: ...

class RemoveSnapshotRequest(_message.Message):
    __slots__ = ("snapshotter", "key")
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    key: str
    def __init__(self, snapshotter: _Optional[str] = ..., key: _Optional[str] = ...) -> None: ...

class CommitSnapshotRequest(_message.Message):
    __slots__ = ("snapshotter", "name", "key", "labels", "parent")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    PARENT_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    name: str
    key: str
    labels: _containers.ScalarMap[str, str]
    parent: str
    def __init__(self, snapshotter: _Optional[str] = ..., name: _Optional[str] = ..., key: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ..., parent: _Optional[str] = ...) -> None: ...

class StatSnapshotRequest(_message.Message):
    __slots__ = ("snapshotter", "key")
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    key: str
    def __init__(self, snapshotter: _Optional[str] = ..., key: _Optional[str] = ...) -> None: ...

class Info(_message.Message):
    __slots__ = ("name", "parent", "kind", "created_at", "updated_at", "labels")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARENT_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    name: str
    parent: str
    kind: Kind
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    labels: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., parent: _Optional[str] = ..., kind: _Optional[_Union[Kind, str]] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., labels: _Optional[_Mapping[str, str]] = ...) -> None: ...

class StatSnapshotResponse(_message.Message):
    __slots__ = ("info",)
    INFO_FIELD_NUMBER: _ClassVar[int]
    info: Info
    def __init__(self, info: _Optional[_Union[Info, _Mapping]] = ...) -> None: ...

class UpdateSnapshotRequest(_message.Message):
    __slots__ = ("snapshotter", "info", "update_mask")
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    INFO_FIELD_NUMBER: _ClassVar[int]
    UPDATE_MASK_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    info: Info
    update_mask: _field_mask_pb2.FieldMask
    def __init__(self, snapshotter: _Optional[str] = ..., info: _Optional[_Union[Info, _Mapping]] = ..., update_mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ...) -> None: ...

class UpdateSnapshotResponse(_message.Message):
    __slots__ = ("info",)
    INFO_FIELD_NUMBER: _ClassVar[int]
    info: Info
    def __init__(self, info: _Optional[_Union[Info, _Mapping]] = ...) -> None: ...

class ListSnapshotsRequest(_message.Message):
    __slots__ = ("snapshotter", "filters")
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    filters: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, snapshotter: _Optional[str] = ..., filters: _Optional[_Iterable[str]] = ...) -> None: ...

class ListSnapshotsResponse(_message.Message):
    __slots__ = ("info",)
    INFO_FIELD_NUMBER: _ClassVar[int]
    info: _containers.RepeatedCompositeFieldContainer[Info]
    def __init__(self, info: _Optional[_Iterable[_Union[Info, _Mapping]]] = ...) -> None: ...

class UsageRequest(_message.Message):
    __slots__ = ("snapshotter", "key")
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    key: str
    def __init__(self, snapshotter: _Optional[str] = ..., key: _Optional[str] = ...) -> None: ...

class UsageResponse(_message.Message):
    __slots__ = ("size", "inodes")
    SIZE_FIELD_NUMBER: _ClassVar[int]
    INODES_FIELD_NUMBER: _ClassVar[int]
    size: int
    inodes: int
    def __init__(self, size: _Optional[int] = ..., inodes: _Optional[int] = ...) -> None: ...

class CleanupRequest(_message.Message):
    __slots__ = ("snapshotter",)
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    snapshotter: str
    def __init__(self, snapshotter: _Optional[str] = ...) -> None: ...
