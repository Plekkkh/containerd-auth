from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TransferRequest(_message.Message):
    __slots__ = ("source", "destination", "options")
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    source: _any_pb2.Any
    destination: _any_pb2.Any
    options: TransferOptions
    def __init__(self, source: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., destination: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., options: _Optional[_Union[TransferOptions, _Mapping]] = ...) -> None: ...

class TransferOptions(_message.Message):
    __slots__ = ("progress_stream",)
    PROGRESS_STREAM_FIELD_NUMBER: _ClassVar[int]
    progress_stream: str
    def __init__(self, progress_stream: _Optional[str] = ...) -> None: ...
