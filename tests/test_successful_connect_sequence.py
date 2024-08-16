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
    State,
    ExternalClientMock,
    status,
    status_payload,
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
        external_client_mock = ExternalClientMock(self.broker, "company_x", "car_a")
        autonomy = device_obj(**AUTONOMY_DEVICE_ID)

        external_client_mock.post(connect_msg("session_id", "company_x", "car_a", [autonomy]), sleep_after=0.5)
        external_client_mock.post(status("session_id", State.CONNECTING, autonomy, 0), sleep_after=0.5)
        external_client_mock.post(command_response("session_id", CmdResponseType.OK, 0))

        payload = status_payload(
            speed=4.5,
            fuel=85,
            car_longitude=49,
            car_latitude=17,
            car_altitude=100,
            next_stop_name="stop_a",
            stop_longitude=49,
            stop_latitude=17.05,
            stop_altitude=200,
        )
        status_msg = status("session_id", State.RUNNING, autonomy, counter=1, payload=payload)
        external_client_mock.post(status_msg)

        time.sleep(1)
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
