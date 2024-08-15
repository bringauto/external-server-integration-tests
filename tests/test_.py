import unittest
import sys
import subprocess
import time
import os

sys.path.append(".")
sys.path.append("lib/fleet-protocol/protobuf/compiled/python")

from tests.broker import MQTTBrokerTest
from InternalProtocol_pb2 import Device as _Device  # type: ignore
from ExternalProtocol_pb2 import (  # type: ignore
    Connect as _Connect,
    CommandResponse as _CommandResponse,
    ConnectResponse as _ConnectResponse,
    ExternalClient as _ExternalClientMsg,
    ExternalServer as _ExternalServerMsg,
    Status as _Status,
    StatusResponse as _StatusResponse,
)


def clear_logs() -> None:
    if os.path.isfile("./log/external-server/external_server.log"):
        os.remove("./log/external-server/external_server.log")
    if os.path.isfile("./log/module-gateway/ModuleGateway.log"):
        os.remove("./log/module-gateway/ModuleGateway.log")


def device(
    module_id: int, device_type: int, device_role: str, device_name: str, priority: int = 0
) -> _Device:
    return _Device(
        module=module_id,
        deviceType=device_type,
        deviceRole=device_role,
        deviceName=device_name,
        priority=priority,
    )


def connect_msg(session_id: str, company: str, car_name: str, devices: list[_Device]) -> _Connect:
    return _Connect(
        sessionId=session_id,
        company=company,
        vehicleName=car_name,
        devices=devices,
    ).SerializeToString()


class Test_Succesfull_Communication_With_Single_Device(unittest.TestCase):

    def setUp(self) -> None:
        clear_logs()
        self.broker = MQTTBrokerTest(start=True)
        subprocess.run(["docker", "compose", "up", "-d"])

    def test_succesfull_connect_sequence_with_a_single_device(self):
        self.broker.publish(
            "company_x/car_a/module-gateway",
            connect_msg("session_id", "company_x", "car_a", [device(1, 0, "autonomy", "Autonomy")]),
        )
        time.sleep(1)


    def tearDown(self):
        subprocess.run(["docker", "compose", "down"])
        self.broker.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
