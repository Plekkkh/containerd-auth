import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HTTPDebug(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DISABLED: _ClassVar[HTTPDebug]
    DEBUG: _ClassVar[HTTPDebug]
    TRACE: _ClassVar[HTTPDebug]
    BOTH: _ClassVar[HTTPDebug]

class AuthType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[AuthType]
    CREDENTIALS: _ClassVar[AuthType]
    REFRESH: _ClassVar[AuthType]
    HEADER: _ClassVar[AuthType]
DISABLED: HTTPDebug
DEBUG: HTTPDebug
TRACE: HTTPDebug
BOTH: HTTPDebug
NONE: AuthType
CREDENTIALS: AuthType
REFRESH: AuthType
HEADER: AuthType

class OCIRegistry(_message.Message):
    __slots__ = ("reference", "resolver")
    REFERENCE_FIELD_NUMBER: _ClassVar[int]
    RESOLVER_FIELD_NUMBER: _ClassVar[int]
    reference: str
    resolver: RegistryResolver
    def __init__(self, reference: _Optional[str] = ..., resolver: _Optional[_Union[RegistryResolver, _Mapping]] = ...) -> None: ...

class RegistryResolver(_message.Message):
    __slots__ = ("auth_stream", "headers", "host_dir", "default_scheme", "http_debug", "logs_stream")
    class HeadersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    AUTH_STREAM_FIELD_NUMBER: _ClassVar[int]
    HEADERS_FIELD_NUMBER: _ClassVar[int]
    HOST_DIR_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_SCHEME_FIELD_NUMBER: _ClassVar[int]
    HTTP_DEBUG_FIELD_NUMBER: _ClassVar[int]
    LOGS_STREAM_FIELD_NUMBER: _ClassVar[int]
    auth_stream: str
    headers: _containers.ScalarMap[str, str]
    host_dir: str
    default_scheme: str
    http_debug: HTTPDebug
    logs_stream: str
    def __init__(self, auth_stream: _Optional[str] = ..., headers: _Optional[_Mapping[str, str]] = ..., host_dir: _Optional[str] = ..., default_scheme: _Optional[str] = ..., http_debug: _Optional[_Union[HTTPDebug, str]] = ..., logs_stream: _Optional[str] = ...) -> None: ...

class AuthRequest(_message.Message):
    __slots__ = ("host", "reference", "wwwauthenticate")
    HOST_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_FIELD_NUMBER: _ClassVar[int]
    WWWAUTHENTICATE_FIELD_NUMBER: _ClassVar[int]
    host: str
    reference: str
    wwwauthenticate: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, host: _Optional[str] = ..., reference: _Optional[str] = ..., wwwauthenticate: _Optional[_Iterable[str]] = ...) -> None: ...

class AuthResponse(_message.Message):
    __slots__ = ("authType", "secret", "username", "expire_at")
    AUTHTYPE_FIELD_NUMBER: _ClassVar[int]
    SECRET_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    EXPIRE_AT_FIELD_NUMBER: _ClassVar[int]
    authType: AuthType
    secret: str
    username: str
    expire_at: _timestamp_pb2.Timestamp
    def __init__(self, authType: _Optional[_Union[AuthType, str]] = ..., secret: _Optional[str] = ..., username: _Optional[str] = ..., expire_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...
