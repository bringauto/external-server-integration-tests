import unittest
import time
import json

from tests._utils.misc import clear_logs
from tests._utils.broker import MQTTBrokerTest
from tests._utils.mocks import (
    ApiClientTest,
    ExternalClientMock,
    docker_compose_up,
    docker_compose_down,
)
from tests._utils.messages import (
    AutonomyError,
    AutonomyStatus,
    CmdResponseType,
    connect_msg,
    command_response,
    device_obj,
    device_id,
    position,
    station,
    Station,
    status,
    DeviceState,
    Device,
)


API_HOST = "http://localhost:8080/v2/protocol"
autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, type=1, role="driving", name="Autonomy")
_broker = MQTTBrokerTest()


class Test_Status_Error(unittest.TestCase):

    def setUp(self) -> None:
        clear_logs()
        self.broker = _broker
        self.ec = ExternalClientMock(self.broker, "company_x", "car_a")
        self.api_client = ApiClientTest(API_HOST, "company_x", "car_a", "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(autonomy=autonomy, ext_client=self.ec)

    def test_empty_error_message_is_not_forwarded_to_api(self):
        error = b""
        payload = AutonomyStatus().SerializeToString()
        self.ec.post(status("id", DeviceState.RUNNING, autonomy, 1, payload, error), sleep=0.1)
        time.sleep(0.5)
        messages = self.api_client.get_statuses()[-1].payload.data.to_dict()
        self.assertEqual(len(messages), 1)

    def test_nonempty_error_message_is_forwarded_to_api(self):
        error = AutonomyError(
            finishedStops=[Station(name="stop_a", position=position())]
        ).SerializeToString()
        payload = AutonomyStatus().SerializeToString()
        self.ec.post(status("id", DeviceState.RUNNING, autonomy, 1, payload, error), sleep=0.1)
        time.sleep(1)
        messages = self.api_client.get_statuses()
        self.assertEqual(messages[-1].payload.message_type, "STATUS_ERROR")
        self.assertEqual(messages[-1].payload.data.to_dict()["finishedStops"][0]["name"], "stop_a")

    def tearDown(self):
        docker_compose_down()

    def _run_connect_sequence(self, autonomy: Device, ext_client: ExternalClientMock) -> None:
        ext_client.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        payload = AutonomyStatus().SerializeToString()
        ext_client.post(status("id", DeviceState.CONNECTING, autonomy, 0, payload), sleep=0.1)
        ext_client.post(command_response("id", CmdResponseType.OK, 0), sleep=0.5)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
