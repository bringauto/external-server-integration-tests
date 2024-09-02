import unittest
import sys
import time

sys.path.append(".")

from tests._utils.broker import MQTTBrokerTest
from tests._utils.mocks import (
    ApiClientTest,
    ExternalClientMock,
    docker_compose_up,
    docker_compose_down
)
from tests._utils.messages import (
    Action,
    AutonomyState,
    AutonomyStatus,
    CmdResponseType,
    DeviceState,
    api_command,
    api_status,
    command_response,
    connect_msg,
    device_id,
    device_obj,
    status,
    station,
    position
)


autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, type=1, role="driving", name="Autonomy")
API_HOST = "http://localhost:8080/v2/protocol"


_broker = MQTTBrokerTest()


class Test_Unsupported_Device(unittest.TestCase):

    def setUp(self) -> None:
        self.broker = _broker
        self.ec = ExternalClientMock(self.broker, "company_x", "car_a")
        self.api_client = ApiClientTest(API_HOST, "company_x", "car_a", "TestAPIKey")
        docker_compose_up()
        self.payload = AutonomyStatus().SerializeToString()

    def test_only_supported_devices_pass_through_connect_seq_and_have_statuses_forwarded_to_api(self):
        unsupported_device = device_obj(module_id=1, type=123456789, role="notdriving", name="UnsupportedDevice", priority=0)
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy, unsupported_device]), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, unsupported_device, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0), sleep=0.1)
        s = self.api_client.get_statuses()
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0].device_id.module_id, autonomy.module)
        self.assertEqual(s[0].device_id.name, "Autonomy")

    def test_only_devices_of_supported_modules_pass_through_connect_seq_and_have_statuses_forwarded_to_api(self):
        unsupp_module_device = device_obj(module_id=123456789, type=1, role="test", name="TestDevice", priority=0)
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy, unsupp_module_device]), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, unsupp_module_device, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0), sleep=0.1)
        s = self.api_client.get_statuses()
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0].device_id.module_id, autonomy.module)
        self.assertEqual(s[0].device_id.name, "Autonomy")

    def tearDown(self):
        docker_compose_down()


if __name__ == "__main__":  # pragma: no cover
    _broker.start()
    unittest.main()
    _broker.stop()
