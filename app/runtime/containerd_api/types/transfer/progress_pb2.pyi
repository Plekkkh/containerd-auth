from types import descriptor_pb2 as _descriptor_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Progress(_message.Message):
    __slots__ = ("event", "name", "parents", "progress", "total", "desc")
    EVENT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARENTS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    DESC_FIELD_NUMBER: _ClassVar[int]
    event: str
    name: str
    parents: _containers.RepeatedScalarFieldContainer[str]
    progress: int
    total: int
    desc: _descriptor_pb2.Descriptor
    def __init__(self, event: _Optional[str] = ..., name: _Optional[str] = ..., parents: _Optional[_Iterable[str]] = ..., progress: _Optional[int] = ..., total: _Optional[int] = ..., desc: _Optional[_Union[_descriptor_pb2.Descriptor, _Mapping]] = ...) -> None: ...
