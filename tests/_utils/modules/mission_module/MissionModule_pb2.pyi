from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class AutonomyCommand(_message.Message):
    __slots__ = ["action", "route", "stops"]

    class Action(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []

    ACTION_FIELD_NUMBER: _ClassVar[int]
    NO_ACTION: AutonomyCommand.Action
    ROUTE_FIELD_NUMBER: _ClassVar[int]
    START: AutonomyCommand.Action
    STOP: AutonomyCommand.Action
    STOPS_FIELD_NUMBER: _ClassVar[int]
    action: AutonomyCommand.Action
    route: str
    stops: _containers.RepeatedCompositeFieldContainer[Station]
    def __init__(
        self,
        stops: _Optional[_Iterable[_Union[Station, _Mapping]]] = ...,
        route: _Optional[str] = ...,
        action: _Optional[_Union[AutonomyCommand.Action, str]] = ...,
    ) -> None: ...

class AutonomyError(_message.Message):
    __slots__ = ["finishedStops"]
    FINISHEDSTOPS_FIELD_NUMBER: _ClassVar[int]
    finishedStops: _containers.RepeatedCompositeFieldContainer[Station]
    def __init__(
        self, finishedStops: _Optional[_Iterable[_Union[Station, _Mapping]]] = ...
    ) -> None: ...

class AutonomyStatus(_message.Message):
    __slots__ = ["nextStop", "state", "telemetry"]

    class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []

    class Telemetry(_message.Message):
        __slots__ = ["fuel", "position", "speed"]
        FUEL_FIELD_NUMBER: _ClassVar[int]
        POSITION_FIELD_NUMBER: _ClassVar[int]
        SPEED_FIELD_NUMBER: _ClassVar[int]
        fuel: float
        position: Position
        speed: float
        def __init__(
            self,
            speed: _Optional[float] = ...,
            fuel: _Optional[float] = ...,
            position: _Optional[_Union[Position, _Mapping]] = ...,
        ) -> None: ...

    DRIVE: AutonomyStatus.State
    ERROR: AutonomyStatus.State
    IDLE: AutonomyStatus.State
    IN_STOP: AutonomyStatus.State
    NEXTSTOP_FIELD_NUMBER: _ClassVar[int]
    OBSTACLE: AutonomyStatus.State
    STATE_FIELD_NUMBER: _ClassVar[int]
    TELEMETRY_FIELD_NUMBER: _ClassVar[int]
    nextStop: Station
    state: AutonomyStatus.State
    telemetry: AutonomyStatus.Telemetry
    def __init__(
        self,
        telemetry: _Optional[_Union[AutonomyStatus.Telemetry, _Mapping]] = ...,
        state: _Optional[_Union[AutonomyStatus.State, str]] = ...,
        nextStop: _Optional[_Union[Station, _Mapping]] = ...,
    ) -> None: ...

class Position(_message.Message):
    __slots__ = ["altitude", "latitude", "longitude"]
    ALTITUDE_FIELD_NUMBER: _ClassVar[int]
    LATITUDE_FIELD_NUMBER: _ClassVar[int]
    LONGITUDE_FIELD_NUMBER: _ClassVar[int]
    altitude: float
    latitude: float
    longitude: float
    def __init__(
        self,
        latitude: _Optional[float] = ...,
        longitude: _Optional[float] = ...,
        altitude: _Optional[float] = ...,
    ) -> None: ...

class Station(_message.Message):
    __slots__ = ["name", "position"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    name: str
    position: Position
    def __init__(
        self,
        name: _Optional[str] = ...,
        position: _Optional[_Union[Position, _Mapping]] = ...,
    ) -> None: ...
