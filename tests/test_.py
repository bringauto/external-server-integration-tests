import unittest
import sys
import subprocess
import time
import os
from google.protobuf.json_format import MessageToDict  # type: ignore

sys.path.append(".")
sys.path.append("lib/mission-module/lib/protobuf-mission-module")

from MissionModule_pb2 import AutonomyStatus, Station, Position  # type: ignore
from tests.broker import MQTTBrokerTest
from tests.api_client import HttpApiClientTest
from tests.utils import (
    command_response,
    connect_msg,
    device_obj,
    CmdResponseType,
    DeviceState,
    CarMsgSenderTest,
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
        # starts the external server and HTTP API
        subprocess.run(["docker", "compose", "up", "--build", "-d"])
        time.sleep(1)
        self.api_client = HttpApiClientTest(
            "http://localhost:8080/v2/protocol", "company_x", "car_a", "TestAPIKey"
        )

    def test_status_sent_after_successful_connect_sequence_from_device_is_available_on_api(self):
        car_msg = CarMsgSenderTest(self.broker, "company_x", "car_a")
        device = device_obj(**AUTONOMY_DEVICE_ID)

        car_msg.post(connect_msg("session_id", "company_x", "car_a", [device]), sleep_after=0.5)
        car_msg.post(status("session_id", DeviceState.CONNECTING, device, b"", 0), sleep_after=0.5)
        car_msg.post(command_response("session_id", CmdResponseType.OK, 0))

        status_payload = AutonomyStatus(
            telemetry=AutonomyStatus.Telemetry(
                speed=4.5, fuel=85, position=Position(longitude=49, latitude=17, altitude=100)
            ),
            state=AutonomyStatus.DRIVE,
            nextStop=Station(
                name="stop_a", position=Position(longitude=49, latitude=17.05, altitude=200)
            ),
        )
        status_msg = status(
            "session_id", DeviceState.RUNNING, device, status_payload.SerializeToString(), counter=1
        )
        car_msg.post(status_msg)

        time.sleep(1)
        data_on_api = self.api_client.get_statuses()[-1].payload.data.to_dict()
        data_sent = MessageToDict(status_payload)

        self.assertEqual(data_on_api["state"], data_sent["state"])
        self.assertDictEqual(data_on_api["telemetry"], data_sent["telemetry"])
        self.assertDictEqual(data_on_api["nextStop"], data_sent["nextStop"])

    def tearDown(self):
        subprocess.run(["docker", "compose", "down"])
        self.broker.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
