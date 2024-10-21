import unittest
import time

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    CmdResponseType,
    DeviceState,
    command_response,
    connect_msg,
    device_id,
    device_obj,
    status,
)


API_HOST = "http://localhost:8080/v2/protocol"
comm_layer = communication_layer()
test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")


class Test_Connection_Sequence(unittest.TestCase):

    def setUp(self) -> None:
        comm_layer.start()
        self.ec_a = ExternalClientMock(comm_layer, "company_x", "car_a")
        self.ec_b = ExternalClientMock(comm_layer, "company_x", "car_b")
        self.api = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up("config_2_cars.json")

    def test_sending_connect_message_statuses_and_commands_makes_successful_connect_sequence(
        self,
    ):
        payload_1 = {"content": "An arbitrary string ...", "timestamp": 111}
        payload_2 = {"content": "Another arbitrary string ...", "timestamp": 222}
        self.ec_a.post(connect_msg("id", "company_x", "car_a", [test_device]), sleep=0.1)
        self.ec_a.post(status("id", "CONNECTING", test_device, 0, payload_1), sleep=0.1)
        self.ec_a.post(command_response("id", CmdResponseType.OK, 0))

        self.ec_b.post(connect_msg("id", "company_x", "car_b", [test_device]), sleep=0.1)
        self.ec_b.post(status("id", "CONNECTING", test_device, 0, payload_2), sleep=0.1)
        self.ec_b.post(command_response("id", CmdResponseType.OK, 0))

        time.sleep(1)

        s_a = self.api.get_statuses("company_x", "car_a")[0]
        self.assertEqual(s_a.device_id.module_id, test_device.module)
        self.assertEqual(s_a.device_id.type, test_device.deviceType)
        self.assertEqual(s_a.device_id.role, test_device.deviceRole)
        self.assertEqual(s_a.device_id.name, test_device.deviceName)
        self.assertEqual(s_a.payload.message_type, "STATUS")
        self.assertEqual(s_a.payload.encoding, "JSON")
        self.assertEqual(s_a.payload.data.to_dict(), payload_1)

        s_b = self.api.get_statuses("company_x", "car_b")[0]
        self.assertEqual(s_b.device_id.module_id, test_device.module)
        self.assertEqual(s_b.device_id.type, test_device.deviceType)
        self.assertEqual(s_b.device_id.role, test_device.deviceRole)
        self.assertEqual(s_b.device_id.name, test_device.deviceName)
        self.assertEqual(s_b.payload.message_type, "STATUS")
        self.assertEqual(s_b.payload.encoding, "JSON")
        self.assertEqual(s_b.payload.data.to_dict(), payload_2)

    def test_one_failing_connect_sequence_does_not_affect_other_car_connect_sequence(self):
        # connect sequence runs only for car_1
        payload_0 = {"content": "An arbitrary string ...", "timestamp": 000}
        payload_1 = {"content": "An arbitrary string ...", "timestamp": 111}
        payload_2 = {"content": "Another arbitrary string ...", "timestamp": 222}
        self.ec_a.post(connect_msg("id", "company_x", "car_a", [test_device]), sleep=0.1)
        self.ec_a.post(status("id", "CONNECTING", test_device, 0, payload_0), sleep=0.1)
        self.ec_a.post(command_response("id", CmdResponseType.OK, 0))

        time.sleep(0.5)

        self.ec_a.post(status("id", "RUNNING", test_device, 0, payload_1), sleep=0.1)
        self.ec_b.post(status("id", "RUNNING", test_device, 0, payload_2), sleep=0.1)

        time.sleep(1)

        # status for car_1 has been succesfully sent
        statuses = self.api.get_statuses("company_x", "car_a")
        self.assertEqual(len(statuses), 2)
        # no status for car_2 - connect sequence failed
        statuses = self.api.get_statuses("company_x", "car_b")
        self.assertEqual(len(statuses), 0)

    def tearDown(self):
        docker_compose_down()
        comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
