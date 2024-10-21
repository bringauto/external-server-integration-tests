import unittest
import time
import sys

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    CmdResponseType,
    connect_msg,
    command_response,
    device_obj,
    device_id,
    status,
    DeviceState,
    Device,
)


API_HOST = "http://localhost:8080/v2/protocol"
test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
_comm_layer = communication_layer()


class Test_Status_Error(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(test_device=test_device, ext_client=self.ec)

    def test_empty_error_message_is_not_forwarded_to_api(self):
        error = b""
        payload = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(status("id", "RUNNING", test_device, 1, payload, error))
        time.sleep(1)
        messages_on_api = self.api_client.get_statuses("company_x", "car_a")
        self.assertFalse(any(m.payload.message_type == "STATUS_ERROR" for m in messages_on_api))

    def test_nonempty_error_message_is_forwarded_to_api(self):
        error = {"error": "An arbitrary error message ..."}
        payload = {"content": "An arbitrary string ...", "timestamp": 111}
        status_msg = status("id", "RUNNING", test_device, 1, payload, error)
        self.ec.post(status_msg)
        time.sleep(1)
        messages = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(messages[-1].payload.message_type, "STATUS_ERROR")
        self.assertEqual(messages[-1].payload.data.to_dict(), error)

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_sequence(self, test_device: Device, ext_client: ExternalClientMock) -> None:
        ext_client.post(connect_msg("id", "company_x", "car_a", [test_device]))
        payload = {"content": "An arbitrary string ...", "timestamp": 000}
        ext_client.post(status("id", "CONNECTING", test_device, 0, payload))
        ext_client.post(command_response("id", CmdResponseType.OK, 0), sleep=0.5)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
