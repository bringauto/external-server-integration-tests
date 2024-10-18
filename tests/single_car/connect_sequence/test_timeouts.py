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
    device_id,
    status,
)


API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()
test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")


class Test_Message_Timeout(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self.msg_timeout = json.load(open("config/external-server/config.json"))["timeout"]

    def test_not_receiving_connect_message_resets_connection_sequence(self):
        time.sleep(self.msg_timeout + 0.2)
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]))
        payload_1 = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(status("id", "CONNECTING", test_device, 0, payload_1))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        payload_2 = {"content": "An arbitrary string XXX", "timestamp": 222}
        self.ec.post(status("id", "RUNNING", test_device, 1, payload_2))
        s = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(s[-1].payload.data.to_dict(), payload_2)

    def test_not_receiving_connecting_status_resets_connection_sequence(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]))
        time.sleep(self.msg_timeout + 1)
        self.ec.post(connect_msg("other_id", "company_x", "car_a", [test_device]))
        payload_1 = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(status("other_id", "CONNECTING", test_device, 0, payload_1))
        self.ec.post(command_response("other_id", CmdResponseType.OK, 0))
        payload_2 = {"content": "An arbitrary string XXX", "timestamp": 222}
        self.ec.post(status("other_id", "RUNNING", test_device, 1, payload_2))
        s = self.api_client.get_statuses("company_x", "car_a", wait=True)
        self.assertEqual(s[-1].payload.data.to_dict(), payload_2)

    def test_not_receiving_first_command_response_resets_connection_sequence(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]))
        payload_1 = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(status("id", "CONNECTING", test_device, 0, payload_1))
        time.sleep(self.msg_timeout + 1)
        self.ec.post(connect_msg("other_id", "company_x", "car_a", [test_device]))
        payload_2 = {"content": "An arbitrary string XXX", "timestamp": 222}
        self.ec.post(status("other_id", "CONNECTING", test_device, 0, payload_2))
        self.ec.post(command_response("other_id", CmdResponseType.OK, 0))
        payload_3 = {"content": "An arbitrary string XXX", "timestamp": 333}
        self.ec.post(status("other_id", "RUNNING", test_device, 1, payload_3))
        s = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(s[-1].payload.data.to_dict(), payload_3)

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_seq(
        self, session_id: str, test_device: Device, ext_client: ExternalClientMock
    ) -> None:
        ext_client.post(connect_msg(session_id, "company_x", "car_a", [test_device]))
        payload = {"content": "An arbitrary string ...", "timestamp": 111}
        ext_client.post(status(session_id, "CONNECTING", test_device, 0, payload))
        ext_client.post(command_response(session_id, CmdResponseType.OK, 0))


if __name__ == "__main__":  # pragma: no cover
    _comm_layer.start()
    unittest.main()
    _comm_layer.stop()
