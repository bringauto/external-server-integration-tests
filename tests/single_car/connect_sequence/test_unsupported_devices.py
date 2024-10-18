import unittest

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    CmdResponseType,
    command_response,
    connect_msg,
    device_id,
    device_obj,
    status,
)


API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()
test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
unsupp_device = device_obj(
    module_id=987654321,
    device_type=123456789,
    role="notdriving",
    name="UnsupportedDevice",
    priority=0,
)


class Test_Unsupported_Device(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()

    def test_only_supported_devices_pass_connect_seq_with_statuses_sent_to_api(self):
        payload = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device, unsupp_device]))
        self.ec.post(status("id", "CONNECTING", test_device, 0, payload))
        self.ec.post(status("id", "CONNECTING", unsupp_device, 0, payload))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        s = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0].device_id.module_id, test_device.module)
        self.assertEqual(s[0].device_id.name, "Test_Device_1")

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    _comm_layer.start()
    unittest.main()
    _comm_layer.stop()
