from typing import Optional
import enum
import time

from tests.broker import MQTTBrokerTest
from InternalProtocol_pb2 import (  # type: ignore
    Device as _Device,
    DeviceStatus as _DeviceStatus,
)
from ExternalProtocol_pb2 import (  # type: ignore
    Connect as _Connect,
    CommandResponse as _CommandResponse,
    ConnectResponse as _ConnectResponse,
    ExternalClient as _ExternalClientMsg,
    ExternalServer as _ExternalServerMsg,
    Status as _Status,
)
from .autonomy_messages.MissionModule_pb2 import AutonomyStatus, Position, Station  # type: ignore


class DeviceState(enum.Enum):
    CONNECTING = _Status.CONNECTING
    RUNNING = _Status.RUNNING
    DISCONNECT = _Status.DISCONNECT
    ERROR = _Status.ERROR


class AutonomyState(enum.Enum):
    DRIVE = AutonomyStatus.DRIVE
    ERROR = AutonomyStatus.ERROR
    IDLE = AutonomyStatus.IDLE
    IN_STOP = AutonomyStatus.IN_STOP
    OBSTACLE = AutonomyStatus.OBSTACLE


class CmdResponseType(enum.Enum):
    OK = _ConnectResponse.OK
    ALREADY_LOGGED = _ConnectResponse.ALREADY_LOGGED


def command_response(
    session_id: str, type: _CommandResponse.Type, counter: int
) -> _ExternalServerMsg:
    return _ExternalClientMsg(
        commandResponse=_CommandResponse(
            sessionId=session_id, type=type.value, messageCounter=counter
        )
    )


def connect_msg(session_id: str, company: str, car_name: str, devices: list[_Device]) -> _Connect:
    return _ExternalClientMsg(
        connect=_Connect(
            sessionId=session_id, company=company, vehicleName=car_name, devices=devices
        )
    )


def device_obj(module_id: int, type: int, role: str, name: str, priority: int = 0) -> _Device:
    return _Device(
        module=module_id,
        deviceType=type,
        deviceRole=role,
        deviceName=name,
        priority=priority,
    )


def status(
    session_id: str,
    state: _Status.DeviceState,
    device: _Device,
    counter: int,
    payload: Optional[AutonomyStatus] = None,
    error_message: Optional[bytes] = None,
) -> _ExternalClientMsg:

    if payload is None:
        payload = AutonomyStatus()
    status = _Status(
        sessionId=session_id,
        deviceState=state.value,
        messageCounter=counter,
        deviceStatus=_DeviceStatus(device=device, statusData=payload.SerializeToString()),
        errorMessage=error_message,
    )
    return _ExternalClientMsg(status=status)


def position(longitude: float = 49.1, latitude: float = 16.05, altitude: float = 123.4) -> Position:
    """Return a Position message for telemetry and stops used for creating messages for tests."""
    return Position(longitude=longitude, latitude=latitude, altitude=altitude)


def telemetry(
    speed: float = 4.5, fuel: float = 0.85, position: Position = position()
) -> AutonomyStatus.Telemetry:
    """Return a telemetry object for the AutonomyStatus message."""
    return AutonomyStatus.Telemetry(speed=speed, fuel=fuel, position=position)


def status_data(
    state: AutonomyState = AutonomyState.DRIVE,
    telemetry: AutonomyStatus.Telemetry = telemetry(),
    next_stop_name: str = "stop_a",
    next_stop_position: Position = position(),
) -> AutonomyStatus:
    """Return a AutonomyStatus message to be included in ExternalClient message used in tests."""
    return AutonomyStatus(
        telemetry=telemetry,
        state=state.value,
        nextStop=Station(name=next_stop_name, position=next_stop_position),
    )


class ExternalClientMock:

    def __init__(self, broker: MQTTBrokerTest, company: str, car: str) -> None:
        self._broker = broker
        self._company = company
        self._car = car

    def post(self, msg: _ExternalClientMsg, sleep: float = 0.0) -> None:
        topic = f"{self._company}/{self._car}/module_gateway"
        msg_str = msg.SerializeToString()
        self._broker.publish(topic, msg_str)
        time.sleep(max(sleep, 0.0))
