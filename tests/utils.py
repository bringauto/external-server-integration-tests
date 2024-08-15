from typing import Optional
import enum

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


class DeviceState(enum.Enum):
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
    ).SerializeToString()


def connect_msg(session_id: str, company: str, car_name: str, devices: list[_Device]) -> _Connect:
    return _ExternalClientMsg(
        connect=_Connect(
            sessionId=session_id, company=company, vehicleName=car_name, devices=devices
        )
    ).SerializeToString()


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
    counter: int,
    device: _Device,
    payload: bytes = b"",
    error_message: Optional[bytes] = None,
) -> _ExternalClientMsg:

    status = _Status(
        sessionId=session_id,
        deviceState=state.value,
        messageCounter=counter,
        deviceStatus=_DeviceStatus(device=device, statusData=payload),
        errorMessage=error_message,
    )
    return _ExternalClientMsg(status=status).SerializeToString()
