import unittest
import sys
import subprocess
import time
import os
from google.protobuf.json_format import MessageToDict  # type: ignore

sys.path.append(".")

from tests.broker import MQTTBrokerTest
from tests.api_client import HttpApiClientTest
from tests.utils import (
    command_response,
    connect_msg,
    device_obj,
    CmdResponseType,
    AutonomyState,
    DeviceState,
    ExternalClientMock,
    position,
    status,
    status_data,
    telemetry,
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
        ext_client = ExternalClientMock(self.broker, "company_x", "car_a")
        autonomy = device_obj(**AUTONOMY_DEVICE_ID)

        # run the connect sequence
        ext_client.post(connect_msg("session_id", "company_x", "car_a", [autonomy]), sleep=0.1)
        ext_client.post(status("session_id", DeviceState.CONNECTING, autonomy, 0), sleep=0.1)
        ext_client.post(command_response("session_id", CmdResponseType.OK, 0))

        # send status message
        payload = status_data(
            state=AutonomyState.DRIVE,
            telemetry=telemetry(4.5, 0.85, position(49.5, 16.14, 123.5)),
            next_stop_name="stop_a",
            next_stop_position=position(49.1, 16.0, 123.4),
        )
        ext_client.post(status("session_id", DeviceState.RUNNING, autonomy, 1, payload), sleep=0.1)

        data_on_api = self.api_client.get_statuses()[-1].payload.data.to_dict()
        data_sent = MessageToDict(payload)
        self.assertEqual(data_on_api["state"], data_sent["state"])
        self.assertDictEqual(data_on_api["telemetry"], data_sent["telemetry"])
        self.assertDictEqual(data_on_api["nextStop"], data_sent["nextStop"])

    def tearDown(self):
        subprocess.run(["docker", "compose", "down"])
        self.broker.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
