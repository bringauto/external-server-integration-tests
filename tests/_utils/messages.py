from typing import Optional, Any, Literal
import enum
import time
import json

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


DeviceStateStr = Literal["CONNECTING", "RUNNING", "DISCONNECT", "ERROR"]
device_status_str: dict[DeviceStateStr, _Status.DeviceState] = {
    "CONNECTING": _Status.CONNECTING,
    "RUNNING": _Status.RUNNING,
    "DISCONNECT": _Status.DISCONNECT,
    "ERROR": _Status.ERROR,
}


class CmdResponseType(enum.Enum):
    OK = _ConnectResponse.OK
    ALREADY_LOGGED = _ConnectResponse.ALREADY_LOGGED


class DeviceState(enum.Enum):
    CONNECTING = _Status.CONNECTING
    RUNNING = _Status.RUNNING
    DISCONNECT = _Status.DISCONNECT
    ERROR = _Status.ERROR


def api_status(device_id: DeviceId, payload: dict[str, Any]) -> Message:
    """Create a status message."""
    payload_dict = {
        "encoding": "JSON",
        "message_type": "STATUS",
        "data": payload,
    }
    message = Message(
        device_id=device_id,
        timestamp=int(time.time() * 1000),
        payload=Payload.from_dict(payload_dict),
    )
    return message


def api_command(device_id: DeviceId, data) -> Message:
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


def device_id(module_id: int, device_type: int, role: str, name: str) -> DeviceId:
    return DeviceId(module_id=module_id, type=device_type, role=role, name=name)


def device_obj(module_id: int, device_type: int, role: str, name: str, priority: int = 0) -> Device:
    return Device(
        module=module_id,
        deviceType=device_type,
        deviceRole=role,
        deviceName=name,
        priority=priority,
    )


def status(
    session_id: str,
    state: DeviceStateStr,
    device: Device,
    counter: int,
    payload: bytes | dict,
    error_message: Optional[bytes] = None,
) -> _ExternalClientMsg:
    """Create a status message sent over MQTT to External Server."""

    payload_bytes = json.dumps(payload).encode() if isinstance(payload, dict) else payload
    error_bytes = (
        json.dumps(error_message).encode() if isinstance(error_message, dict) else error_message
    )
    status = _Status(
        sessionId=session_id,
        deviceState=device_status_str[state],
        messageCounter=counter,
        deviceStatus=DeviceStatus(device=device, statusData=payload_bytes),
        errorMessage=error_bytes,
    )
    return _ExternalClientMsg(status=status)
