import unittest
import sys
import subprocess
import time
import os

sys.path.append(".")
sys.path.append("lib/fleet-protocol/protobuf/compiled/python")

from tests.broker import MQTTBrokerTest
from tests.utils import (
    command_response,
    connect_msg,
    device_obj,
    CmdResponseType,
    DeviceState,
    status,
)


def clear_logs() -> None:
    if os.path.isfile("./log/external-server/external_server.log"):
        os.remove("./log/external-server/external_server.log")
    if os.path.isfile("./log/module-gateway/ModuleGateway.log"):
        os.remove("./log/module-gateway/ModuleGateway.log")


AUTONOMY_DEVICE_ID = {"module_id": 1, "type": 1, "role": "driving", "name": "Autonomy"}


class Test_Succesfull_Communication_With_Single_Device(unittest.TestCase):

    def setUp(self) -> None:
        clear_logs()
        self.broker = MQTTBrokerTest(start=True)
        subprocess.run(["docker", "compose", "up", "--build", "-d"])
        time.sleep(2)

    def test_succesfull_connect_sequence_with_a_single_device(self):
        device = device_obj(**AUTONOMY_DEVICE_ID)
        self.broker.publish(
            "company_x/car_a/module_gateway",
            connect_msg("session_id", "company_x", "car_a", [device]),
        )
        time.sleep(1)
        self.broker.publish(
            "company_x/car_a/module_gateway",
            status(
                "session_id", state=DeviceState.CONNECTING, device=device, payload=b"", counter=0
            ),
        )
        time.sleep(2)
        self.broker.publish(
            "company_x/car_a/module_gateway",
            command_response("session_id", type=CmdResponseType.OK, counter=0),
        )
        time.sleep(5)

    def tearDown(self):
        subprocess.run(["docker", "compose", "down"])
        self.broker.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
