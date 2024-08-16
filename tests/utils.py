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


class State(enum.Enum):
    CONNECTING = _Status.CONNECTING
    RUNNING = _Status.RUNNING
    DISCONNECT = _Status.DISCONNECT
    ERROR = _Status.ERROR


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


def status_payload(
    state: AutonomyStatus.State = AutonomyStatus.DRIVE,
    speed: float = 1.0,
    fuel: float = 0.65,
    car_longitude: float = 49.1,
    car_latitude: float = 17.05,
    car_altitude: float = 123.4,
    next_stop_name: str = "stop_a",
    stop_longitude: float = 49.2,
    stop_latitude: float = 17.1,
    stop_altitude: float = 200.0
) -> AutonomyStatus:

    return AutonomyStatus(
        telemetry=AutonomyStatus.Telemetry(
            speed=speed,
            fuel=fuel,
            position=Position(
                longitude=car_longitude,
                latitude=car_latitude,
                altitude=car_altitude
            )
        ),
        state=state,
        nextStop=Station(
            name=next_stop_name,
            position=Position(
                longitude=stop_longitude,
                latitude=stop_latitude,
                altitude=stop_altitude
            )
        )
    )



class ExternalClientMock:

    def __init__(self, broker: MQTTBrokerTest, company: str, car: str) -> None:
        self._broker = broker
        self._company = company
        self._car = car

    def post(self, msg: _ExternalClientMsg, sleep_after: float = 0.0) -> None:
        topic = f"{self._company}/{self._car}/module_gateway"
        msg_str = msg.SerializeToString()
        self._broker.publish(topic, msg_str)
        time.sleep(max(sleep_after, 0.0))
