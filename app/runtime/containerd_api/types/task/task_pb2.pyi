import datetime

from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[Status]
    CREATED: _ClassVar[Status]
    RUNNING: _ClassVar[Status]
    STOPPED: _ClassVar[Status]
    PAUSED: _ClassVar[Status]
    PAUSING: _ClassVar[Status]
UNKNOWN: Status
CREATED: Status
RUNNING: Status
STOPPED: Status
PAUSED: Status
PAUSING: Status

class Process(_message.Message):
    __slots__ = ("container_id", "id", "pid", "status", "stdin", "stdout", "stderr", "terminal", "exit_status", "exited_at")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STDIN_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    TERMINAL_FIELD_NUMBER: _ClassVar[int]
    EXIT_STATUS_FIELD_NUMBER: _ClassVar[int]
    EXITED_AT_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    id: str
    pid: int
    status: Status
    stdin: str
    stdout: str
    stderr: str
    terminal: bool
    exit_status: int
    exited_at: _timestamp_pb2.Timestamp
    def __init__(self, container_id: _Optional[str] = ..., id: _Optional[str] = ..., pid: _Optional[int] = ..., status: _Optional[_Union[Status, str]] = ..., stdin: _Optional[str] = ..., stdout: _Optional[str] = ..., stderr: _Optional[str] = ..., terminal: _Optional[bool] = ..., exit_status: _Optional[int] = ..., exited_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ProcessInfo(_message.Message):
    __slots__ = ("pid", "info")
    PID_FIELD_NUMBER: _ClassVar[int]
    INFO_FIELD_NUMBER: _ClassVar[int]
    pid: int
    info: _any_pb2.Any
    def __init__(self, pid: _Optional[int] = ..., info: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
