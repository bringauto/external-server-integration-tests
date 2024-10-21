import unittest
import time

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    connect_msg,
    command_response,
    device_obj,
    device_id,
    status,
    CmdResponseType,
)


API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()
test_device_1 = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_1_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_2 = device_obj(module_id=3, device_type=2, role="test_device_2", name="Test_Device_2")


class Test_Device_Disconnection(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()

    def test_statuses_of_disconnected_device_are_not_forwarded_to_api(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device_1, test_device_2]))
        payload_1 = {"content": "test message 1"}
        payload_2 = {"content": "test message 2"}
        payload_disconnect = {"content": "test message disconnect"}
        self.ec.post(status("id", "CONNECTING", test_device_1, 0, payload_1))
        self.ec.post(status("id", "CONNECTING", test_device_2, 1, payload_2), sleep=0.5)
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))

        time.sleep(0.5)
        self.ec.post(status("id", "DISCONNECT", test_device_1, 2, payload_disconnect))

        time.sleep(0.5)
        timestamp = int(1000 * time.time())

        payload_3 = {"content": "test message 3"}
        payload_4 = {"content": "test message 4"}
        payload_5 = {"content": "test message 5"}
        payload_6 = {"content": "test message 6"}

        self.ec.post(status("id", "RUNNING", test_device_2, 3, payload_3))
        self.ec.post(status("id", "RUNNING", test_device_1, 4, payload_4))
        self.ec.post(status("id", "RUNNING", test_device_2, 5, payload_5))
        self.ec.post(status("id", "RUNNING", test_device_1, 6, payload_6))

        time.sleep(1)
        statuses = self.api_client.get_statuses("company_x", "car_a", since=timestamp)
        self.assertEqual(len(statuses), 2)
        self.assertNotIn(test_device_1_id, [status.device_id for status in statuses])

    def test_statuses_of_connected_device_are_again_forwarded_to_api(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device_1, test_device_2]))
        payload = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(status("id", "CONNECTING", test_device_1, 0, payload))
        self.ec.post(status("id", "CONNECTING", test_device_2, 1, payload))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))

        time.sleep(0.1)
        self.ec.post(status("id", "DISCONNECT", test_device_1, 2, payload))

        time.sleep(0.1)
        self.ec.post(status("id", "CONNECTING", test_device_1, 3, payload))

        time.sleep(0.1)
        self.ec.post(status("id", "RUNNING", test_device_2, 4, payload))
        self.ec.post(status("id", "RUNNING", test_device_1, 5, payload))
        self.ec.post(status("id", "RUNNING", test_device_2, 6, payload))
        self.ec.post(status("id", "RUNNING", test_device_1, 7, payload))

    def test_connection_sequence_is_repeated_if_all_devices_disconnect(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device_1, test_device_2]))
        payload = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(status("id", "CONNECTING", test_device_1, 0, payload))
        self.ec.post(status("id", "CONNECTING", test_device_2, 1, payload))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))

        time.sleep(0.5)
        self.ec.post(status("id", "DISCONNECT", test_device_1, 2, payload))
        self.ec.post(status("id", "DISCONNECT", test_device_2, 3, payload))

        time.sleep(2)
        self.ec.post(connect_msg("new_id", "company_x", "car_a", [test_device_1, test_device_2]))
        payload = {"content": "An arbitrary string ...", "timestamp": 222}
        self.ec.post(status("new_id", "CONNECTING", test_device_1, 2, payload))
        self.ec.post(status("new_id", "CONNECTING", test_device_2, 3, payload))
        self.ec.post(command_response("new_id", CmdResponseType.OK, 2))
        self.ec.post(command_response("new_id", CmdResponseType.OK, 3))

        time.sleep(0.5)
        timestamp = int(1000 * time.time())
        payload = {"content": "An arbitrary string ...", "timestamp": 333}
        self.ec.post(status("new_id", "RUNNING", test_device_1, 4, payload))

        statuses = self.api_client.get_statuses("company_x", "car_a", since=timestamp)
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0].payload.data.to_dict(), payload)

    def test_device_is_disconnected_immediatelly_after_receving_command_response_even_though_not_in_order(
        self,
    ):
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device_1, test_device_2]))
        payload_1 = {"content": "An arbitrary string ...", "timestamp": 111}
        payload_2 = {"content": "Another arbitrary string ...", "timestamp": 222}
        self.ec.post(status("id", "CONNECTING", test_device_1, 0, payload_1))
        self.ec.post(status("id", "CONNECTING", test_device_2, 1, payload_2))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))

    def tearDown(self) -> None:
        docker_compose_down()
        _comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
