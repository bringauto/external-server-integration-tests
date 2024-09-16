from typing import Optional
import enum
import time

from google.protobuf.json_format import MessageToDict  # type: ignore

from InternalProtocol_pb2 import (  # type: ignore
    Device,
    DeviceStatus as DeviceStatus,
)
from ExternalProtocol_pb2 import (  # type: ignore
    Connect as _Connect,
    CommandResponse as _CommandResponse,
    ConnectResponse as _ConnectResponse,
    ExternalClient as _ExternalClientMsg,
    ExternalServer as _ExternalServerMsg,
    Status as _Status,
)
from fleet_http_client_python import Message, Payload, DeviceId  # type: ignore
from .modules.mission_module.MissionModule_pb2 import (  # type: ignore
    AutonomyCommand,
    AutonomyError,
    AutonomyStatus,
    Position,
    Station,
)


class Action(enum.Enum):
    STOP = AutonomyCommand.STOP
    START = AutonomyCommand.START
    NO_ACTION = AutonomyCommand.NO_ACTION


class AutonomyState(enum.Enum):
    DRIVE = AutonomyStatus.DRIVE
    ERROR = AutonomyStatus.ERROR
    IDLE = AutonomyStatus.IDLE
    IN_STOP = AutonomyStatus.IN_STOP
    OBSTACLE = AutonomyStatus.OBSTACLE


class CmdResponseType(enum.Enum):
    OK = _ConnectResponse.OK
    ALREADY_LOGGED = _ConnectResponse.ALREADY_LOGGED


class DeviceState(enum.Enum):
    CONNECTING = _Status.CONNECTING
    RUNNING = _Status.RUNNING
    DISCONNECT = _Status.DISCONNECT
    ERROR = _Status.ERROR


def station(name: str, position: Position) -> dict:
    return {"name": name, "position": MessageToDict(position)}


def api_autonomy_command(
    device_id: DeviceId, action: Action, stops: list[Station], route: str
) -> Message:
    """Create a command message."""
    command_data = AutonomyCommand(stops=stops, action=action.value, route=route)
    payload_dict = {
        "encoding": "JSON",
        "message_type": "COMMAND",
        "data": MessageToDict(command_data),
    }
    message = Message(
        device_id=device_id,
        timestamp=int(time.time() * 1000),
        payload=Payload.from_dict(payload_dict),
    )
    return message


def api_autonomy_status(
    device_id: DeviceId,
    state: AutonomyState,
    telemetry: AutonomyStatus.Telemetry,
    next_stop: Station,
) -> Message:
    """Create a status message."""
    status_data = AutonomyStatus(telemetry=telemetry, state=state.value, nextStop=next_stop)
    payload_dict = {
        "encoding": "JSON",
        "message_type": "STATUS",
        "data": MessageToDict(status_data),
    }
    message = Message(
        device_id=device_id,
        timestamp=int(time.time() * 1000),
        payload=Payload.from_dict(payload_dict),
    )
    return message


def api_io_command(device_id: DeviceId, data) -> Message:
    """Create a command message."""
    payload_dict = {
        "encoding": "JSON",
        "message_type": "COMMAND",
        "data": data,
    }
    message = Message(
        device_id=device_id,
        timestamp=int(time.time() * 1000),
        payload=Payload.from_dict(payload_dict),
    )
    return message


def command_response(
    session_id: str, type: _CommandResponse.Type, counter: int
) -> _ExternalServerMsg:
    return _ExternalClientMsg(
        commandResponse=_CommandResponse(
            sessionId=session_id, type=type.value, messageCounter=counter
        )
    )


def connect_msg(session_id: str, company: str, car_name: str, devices: list[Device]) -> _Connect:
    return _ExternalClientMsg(
        connect=_Connect(
            sessionId=session_id, company=company, vehicleName=car_name, devices=devices
        )
    )


def device_id(module_id: int, type: int, role: str, name: str, **kwargs) -> DeviceId:
    return DeviceId(module_id=module_id, type=type, role=role, name=name)


def device_obj(module_id: int, type: int, role: str, name: str, priority: int = 0) -> Device:
    return Device(
        module=module_id,
        deviceType=type,
        deviceRole=role,
        deviceName=name,
        priority=priority,
    )


def status(
    session_id: str,
    state: _Status.DeviceState,
    device: Device,
    counter: int,
    payload: bytes,
    error_message: Optional[bytes] = None,
) -> _ExternalClientMsg:
    """Create a status message sent over MQTT to External Server."""

    status = _Status(
        sessionId=session_id,
        deviceState=state.value,
        messageCounter=counter,
        deviceStatus=DeviceStatus(device=device, statusData=payload),
        errorMessage=error_message,
    )
    return _ExternalClientMsg(status=status)


def position(longitude: float = 49.1, latitude: float = 16.05, altitude: float = 123.4) -> Position:
    """Return a Position message for telemetry and stops used for creating messages for tests."""
    return Position(longitude=longitude, latitude=latitude, altitude=altitude)


def telemetry(
    speed: float = 4.5, fuel: float = 0.5, position: Position = position()
) -> AutonomyStatus.Telemetry:
    """Return a telemetry object for the AutonomyStatus message."""
    return AutonomyStatus.Telemetry(speed=speed, fuel=fuel, position=position)


def autonomy_status_data(
    state: AutonomyState = AutonomyState.DRIVE,
    telemetry: AutonomyStatus.Telemetry = telemetry(),
    next_stop: Station = Station(
        name="stop_a",
        position=Position(latitude=49.1, longitude=16.0, altitude=123.4),
    ),
) -> AutonomyStatus:
    """Return a AutonomyStatus message to be included in ExternalClient message used in tests."""
    return AutonomyStatus(telemetry=telemetry, state=state.value, nextStop=next_stop)
