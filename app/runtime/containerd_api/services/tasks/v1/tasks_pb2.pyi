import datetime

from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from types import descriptor_pb2 as _descriptor_pb2
from types import metrics_pb2 as _metrics_pb2
from types import mount_pb2 as _mount_pb2
from types.task import task_pb2 as _task_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateTaskRequest(_message.Message):
    __slots__ = ("container_id", "rootfs", "stdin", "stdout", "stderr", "terminal", "checkpoint", "options", "runtime_path", "task_api_address", "task_api_version")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    ROOTFS_FIELD_NUMBER: _ClassVar[int]
    STDIN_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    TERMINAL_FIELD_NUMBER: _ClassVar[int]
    CHECKPOINT_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    RUNTIME_PATH_FIELD_NUMBER: _ClassVar[int]
    TASK_API_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    TASK_API_VERSION_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    rootfs: _containers.RepeatedCompositeFieldContainer[_mount_pb2.Mount]
    stdin: str
    stdout: str
    stderr: str
    terminal: bool
    checkpoint: _descriptor_pb2.Descriptor
    options: _any_pb2.Any
    runtime_path: str
    task_api_address: str
    task_api_version: int
    def __init__(self, container_id: _Optional[str] = ..., rootfs: _Optional[_Iterable[_Union[_mount_pb2.Mount, _Mapping]]] = ..., stdin: _Optional[str] = ..., stdout: _Optional[str] = ..., stderr: _Optional[str] = ..., terminal: _Optional[bool] = ..., checkpoint: _Optional[_Union[_descriptor_pb2.Descriptor, _Mapping]] = ..., options: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., runtime_path: _Optional[str] = ..., task_api_address: _Optional[str] = ..., task_api_version: _Optional[int] = ...) -> None: ...

class CreateTaskResponse(_message.Message):
    __slots__ = ("container_id", "pid")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    pid: int
    def __init__(self, container_id: _Optional[str] = ..., pid: _Optional[int] = ...) -> None: ...

class StartRequest(_message.Message):
    __slots__ = ("container_id", "exec_id")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_ID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    exec_id: str
    def __init__(self, container_id: _Optional[str] = ..., exec_id: _Optional[str] = ...) -> None: ...

class StartResponse(_message.Message):
    __slots__ = ("pid",)
    PID_FIELD_NUMBER: _ClassVar[int]
    pid: int
    def __init__(self, pid: _Optional[int] = ...) -> None: ...

class DeleteTaskRequest(_message.Message):
    __slots__ = ("container_id",)
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    def __init__(self, container_id: _Optional[str] = ...) -> None: ...

class DeleteResponse(_message.Message):
    __slots__ = ("id", "pid", "exit_status", "exited_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    EXIT_STATUS_FIELD_NUMBER: _ClassVar[int]
    EXITED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    pid: int
    exit_status: int
    exited_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., pid: _Optional[int] = ..., exit_status: _Optional[int] = ..., exited_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class DeleteProcessRequest(_message.Message):
    __slots__ = ("container_id", "exec_id")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_ID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    exec_id: str
    def __init__(self, container_id: _Optional[str] = ..., exec_id: _Optional[str] = ...) -> None: ...

class GetRequest(_message.Message):
    __slots__ = ("container_id", "exec_id")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_ID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    exec_id: str
    def __init__(self, container_id: _Optional[str] = ..., exec_id: _Optional[str] = ...) -> None: ...

class GetResponse(_message.Message):
    __slots__ = ("process",)
    PROCESS_FIELD_NUMBER: _ClassVar[int]
    process: _task_pb2.Process
    def __init__(self, process: _Optional[_Union[_task_pb2.Process, _Mapping]] = ...) -> None: ...

class ListTasksRequest(_message.Message):
    __slots__ = ("filter",)
    FILTER_FIELD_NUMBER: _ClassVar[int]
    filter: str
    def __init__(self, filter: _Optional[str] = ...) -> None: ...

class ListTasksResponse(_message.Message):
    __slots__ = ("tasks",)
    TASKS_FIELD_NUMBER: _ClassVar[int]
    tasks: _containers.RepeatedCompositeFieldContainer[_task_pb2.Process]
    def __init__(self, tasks: _Optional[_Iterable[_Union[_task_pb2.Process, _Mapping]]] = ...) -> None: ...

class KillRequest(_message.Message):
    __slots__ = ("container_id", "exec_id", "signal", "all")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_ID_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_FIELD_NUMBER: _ClassVar[int]
    ALL_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    exec_id: str
    signal: int
    all: bool
    def __init__(self, container_id: _Optional[str] = ..., exec_id: _Optional[str] = ..., signal: _Optional[int] = ..., all: _Optional[bool] = ...) -> None: ...

class ExecProcessRequest(_message.Message):
    __slots__ = ("container_id", "stdin", "stdout", "stderr", "terminal", "spec", "exec_id")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    STDIN_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    TERMINAL_FIELD_NUMBER: _ClassVar[int]
    SPEC_FIELD_NUMBER: _ClassVar[int]
    EXEC_ID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    stdin: str
    stdout: str
    stderr: str
    terminal: bool
    spec: _any_pb2.Any
    exec_id: str
    def __init__(self, container_id: _Optional[str] = ..., stdin: _Optional[str] = ..., stdout: _Optional[str] = ..., stderr: _Optional[str] = ..., terminal: _Optional[bool] = ..., spec: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., exec_id: _Optional[str] = ...) -> None: ...

class ExecProcessResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResizePtyRequest(_message.Message):
    __slots__ = ("container_id", "exec_id", "width", "height")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_ID_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    exec_id: str
    width: int
    height: int
    def __init__(self, container_id: _Optional[str] = ..., exec_id: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ...) -> None: ...

class CloseIORequest(_message.Message):
    __slots__ = ("container_id", "exec_id", "stdin")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_ID_FIELD_NUMBER: _ClassVar[int]
    STDIN_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    exec_id: str
    stdin: bool
    def __init__(self, container_id: _Optional[str] = ..., exec_id: _Optional[str] = ..., stdin: _Optional[bool] = ...) -> None: ...

class PauseTaskRequest(_message.Message):
    __slots__ = ("container_id",)
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    def __init__(self, container_id: _Optional[str] = ...) -> None: ...

class ResumeTaskRequest(_message.Message):
    __slots__ = ("container_id",)
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    def __init__(self, container_id: _Optional[str] = ...) -> None: ...

class ListPidsRequest(_message.Message):
    __slots__ = ("container_id",)
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    def __init__(self, container_id: _Optional[str] = ...) -> None: ...

class ListPidsResponse(_message.Message):
    __slots__ = ("processes",)
    PROCESSES_FIELD_NUMBER: _ClassVar[int]
    processes: _containers.RepeatedCompositeFieldContainer[_task_pb2.ProcessInfo]
    def __init__(self, processes: _Optional[_Iterable[_Union[_task_pb2.ProcessInfo, _Mapping]]] = ...) -> None: ...

class CheckpointTaskRequest(_message.Message):
    __slots__ = ("container_id", "parent_checkpoint", "options")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_CHECKPOINT_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    parent_checkpoint: str
    options: _any_pb2.Any
    def __init__(self, container_id: _Optional[str] = ..., parent_checkpoint: _Optional[str] = ..., options: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class CheckpointTaskResponse(_message.Message):
    __slots__ = ("descriptors",)
    DESCRIPTORS_FIELD_NUMBER: _ClassVar[int]
    descriptors: _containers.RepeatedCompositeFieldContainer[_descriptor_pb2.Descriptor]
    def __init__(self, descriptors: _Optional[_Iterable[_Union[_descriptor_pb2.Descriptor, _Mapping]]] = ...) -> None: ...

class UpdateTaskRequest(_message.Message):
    __slots__ = ("container_id", "resources", "annotations")
    class AnnotationsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    ANNOTATIONS_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    resources: _any_pb2.Any
    annotations: _containers.ScalarMap[str, str]
    def __init__(self, container_id: _Optional[str] = ..., resources: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., annotations: _Optional[_Mapping[str, str]] = ...) -> None: ...

class MetricsRequest(_message.Message):
    __slots__ = ("filters",)
    FILTERS_FIELD_NUMBER: _ClassVar[int]
    filters: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, filters: _Optional[_Iterable[str]] = ...) -> None: ...

class MetricsResponse(_message.Message):
    __slots__ = ("metrics",)
    METRICS_FIELD_NUMBER: _ClassVar[int]
    metrics: _containers.RepeatedCompositeFieldContainer[_metrics_pb2.Metric]
    def __init__(self, metrics: _Optional[_Iterable[_Union[_metrics_pb2.Metric, _Mapping]]] = ...) -> None: ...

class WaitRequest(_message.Message):
    __slots__ = ("container_id", "exec_id")
    CONTAINER_ID_FIELD_NUMBER: _ClassVar[int]
    EXEC_ID_FIELD_NUMBER: _ClassVar[int]
    container_id: str
    exec_id: str
    def __init__(self, container_id: _Optional[str] = ..., exec_id: _Optional[str] = ...) -> None: ...

class WaitResponse(_message.Message):
    __slots__ = ("exit_status", "exited_at")
    EXIT_STATUS_FIELD_NUMBER: _ClassVar[int]
    EXITED_AT_FIELD_NUMBER: _ClassVar[int]
    exit_status: int
    exited_at: _timestamp_pb2.Timestamp
    def __init__(self, exit_status: _Optional[int] = ..., exited_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
