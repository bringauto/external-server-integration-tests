import unittest
import time
import json

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    Device,
    command_response,
    connect_msg,
    device_obj,
    CmdResponseType,
    AutonomyStatus,
    AutonomyState,
    device_id,
    DeviceState,
    status,
)


autonomy = device_obj(module_id=1, device_type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, device_type=1, role="driving", name="Autonomy")
API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()


class Test_Message_Timeout(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self.msg_timeout = json.load(open("config/external-server/config.json"))["timeout"]

    def test_not_receiving_connect_message_resets_connection_sequence(self):
        time.sleep(self.msg_timeout + 0.2)
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.2)
        payload = AutonomyStatus().SerializeToString()
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, payload), sleep=0.2)
        self.ec.post(command_response("id", CmdResponseType.OK, 0), sleep=0.1)

        payload = AutonomyStatus(state=AutonomyState.OBSTACLE.value).SerializeToString()
        self.ec.post(status("id", DeviceState.RUNNING, autonomy, 1, payload), sleep=0.1)

        time.sleep(0.5)
        s = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(s[-1].payload.data.to_dict()["state"], "OBSTACLE")

    def test_not_receiving_connecting_status_resets_connection_sequence(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]))

        time.sleep(self.msg_timeout + 3)
        self.ec.post(connect_msg("other_id", "company_x", "car_a", [autonomy]), sleep=0.1)
        payload = AutonomyStatus().SerializeToString()
        self.ec.post(status("other_id", DeviceState.CONNECTING, autonomy, 0, payload), sleep=0.1)
        self.ec.post(command_response("other_id", CmdResponseType.OK, 0), sleep=0.5)

        payload = AutonomyStatus(state=AutonomyState.OBSTACLE.value).SerializeToString()
        self.ec.post(status("other_id", DeviceState.RUNNING, autonomy, 1, payload), sleep=0.1)
        time.sleep(1)
        s = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(s[-1].payload.data.to_dict()["state"], "OBSTACLE")

    def test_not_receiving_first_command_response_resets_connection_sequence(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]))
        payload = AutonomyStatus().SerializeToString()
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, payload), sleep=0.1)
        time.sleep(self.msg_timeout + 1)

        self.ec.post(connect_msg("other_id", "company_x", "car_a", [autonomy]), sleep=0.1)
        payload = AutonomyStatus().SerializeToString()
        self.ec.post(status("other_id", DeviceState.CONNECTING, autonomy, 0, payload), sleep=0.1)
        self.ec.post(command_response("other_id", CmdResponseType.OK, 0), sleep=0.1)

        payload = AutonomyStatus(state=AutonomyState.OBSTACLE.value).SerializeToString()
        self.ec.post(status("other_id", DeviceState.RUNNING, autonomy, 1, payload), sleep=0.1)
        time.sleep(1)
        s = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(s[-1].payload.data.to_dict()["state"], "OBSTACLE")

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_seq(
        self, session_id: str, autonomy: Device, ext_client: ExternalClientMock
    ) -> None:
        ext_client.post(connect_msg(session_id, "company_x", "car_a", [autonomy]), sleep=0.1)
        payload = AutonomyStatus().SerializeToString()
        ext_client.post(status(session_id, DeviceState.CONNECTING, autonomy, 0, payload), sleep=0.1)
        ext_client.post(command_response(session_id, CmdResponseType.OK, 0), sleep=0.5)


if __name__ == "__main__":  # pragma: no cover
    _comm_layer.start()
    unittest.main()
    _comm_layer.stop()
