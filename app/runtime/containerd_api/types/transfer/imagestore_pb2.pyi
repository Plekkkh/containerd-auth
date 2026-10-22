from types import platform_pb2 as _platform_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ImageStore(_message.Message):
    __slots__ = ("name", "labels", "platforms", "all_metadata", "manifest_limit", "extra_references", "unpacks")
    class LabelsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    PLATFORMS_FIELD_NUMBER: _ClassVar[int]
    ALL_METADATA_FIELD_NUMBER: _ClassVar[int]
    MANIFEST_LIMIT_FIELD_NUMBER: _ClassVar[int]
    EXTRA_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    UNPACKS_FIELD_NUMBER: _ClassVar[int]
    name: str
    labels: _containers.ScalarMap[str, str]
    platforms: _containers.RepeatedCompositeFieldContainer[_platform_pb2.Platform]
    all_metadata: bool
    manifest_limit: int
    extra_references: _containers.RepeatedCompositeFieldContainer[ImageReference]
    unpacks: _containers.RepeatedCompositeFieldContainer[UnpackConfiguration]
    def __init__(self, name: _Optional[str] = ..., labels: _Optional[_Mapping[str, str]] = ..., platforms: _Optional[_Iterable[_Union[_platform_pb2.Platform, _Mapping]]] = ..., all_metadata: _Optional[bool] = ..., manifest_limit: _Optional[int] = ..., extra_references: _Optional[_Iterable[_Union[ImageReference, _Mapping]]] = ..., unpacks: _Optional[_Iterable[_Union[UnpackConfiguration, _Mapping]]] = ...) -> None: ...

class UnpackConfiguration(_message.Message):
    __slots__ = ("platform", "snapshotter")
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOTTER_FIELD_NUMBER: _ClassVar[int]
    platform: _platform_pb2.Platform
    snapshotter: str
    def __init__(self, platform: _Optional[_Union[_platform_pb2.Platform, _Mapping]] = ..., snapshotter: _Optional[str] = ...) -> None: ...

class ImageReference(_message.Message):
    __slots__ = ("name", "is_prefix", "allow_overwrite", "add_digest", "skip_named_digest")
    NAME_FIELD_NUMBER: _ClassVar[int]
    IS_PREFIX_FIELD_NUMBER: _ClassVar[int]
    ALLOW_OVERWRITE_FIELD_NUMBER: _ClassVar[int]
    ADD_DIGEST_FIELD_NUMBER: _ClassVar[int]
    SKIP_NAMED_DIGEST_FIELD_NUMBER: _ClassVar[int]
    name: str
    is_prefix: bool
    allow_overwrite: bool
    add_digest: bool
    skip_named_digest: bool
    def __init__(self, name: _Optional[str] = ..., is_prefix: _Optional[bool] = ..., allow_overwrite: _Optional[bool] = ..., add_digest: _Optional[bool] = ..., skip_named_digest: _Optional[bool] = ...) -> None: ...
