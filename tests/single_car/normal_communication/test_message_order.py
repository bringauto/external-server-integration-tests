import unittest
import time
from concurrent import futures
import sys

sys.path.append("lib/fleet-protocol/protobuf/compiled/python")

from google.protobuf.json_format import MessageToDict  # type: ignore

from tests._utils.messages import (
    api_command,
    api_status,
    CmdResponseType,
    _ExternalServerMsg,
    connect_msg,
    status,
    command_response,
    device_obj,
    device_id,
)
from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down


API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()
test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")


class Test_Message_Order(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(car_name="car_a")
        time.sleep(0.5)

    def test_statuses_received_in_incorrect_order_are_published_to_api_in_correct_order(self):
        payload_1 = {"content": "An arbitrary string ...", "timestamp": 111}
        payload_2 = {"content": "Another arbitrary string ...", "timestamp": 222}
        payload_3 = {"content": "Yet another arbitrary string ...", "timestamp": 333}
        self.ec.post(status("id", "RUNNING", test_device, 1, payload_1))
        self.ec.post(status("id", "RUNNING", test_device, 3, payload_3))

        statuses = self.api_client.get_statuses("company_x", "car_a")
        # only the status from connect sequence and the first status are published to the API
        # status with counter value 3 is not published - counter value 2 is missing
        self.assertEqual(len(statuses), 2)
        self.assertEqual(statuses[1].payload.data.to_dict(), payload_1)

        self.ec.post(status("id", "RUNNING", test_device, 2, payload_2), sleep=0.5)
        statuses = self.api_client.get_statuses("company_x", "car_a")
        # all statuses are now published to the API in correct order
        self.assertEqual(len(statuses), 4)
        self.assertEqual(statuses[2].payload.data.to_dict(), payload_2)
        self.assertEqual(statuses[3].payload.data.to_dict(), payload_3)

    def test_commands_are_always_published_regardless_of_receiving_command_responses(
        self,
    ):

        command_payload_1 = {"content": "An arbitrary command ...", "timestamp": 111}
        command_payload_2 = {"content": "Another arbitrary command ...", "timestamp": 222}
        command_payload_3 = {"content": "Yet another arbitrary command ...", "timestamp": 333}
        with futures.ThreadPoolExecutor() as executor:
            f1 = executor.submit(self.ec.get, n=3)
            self.api_client.post_commands(
                "company_x",
                "car_a",
                api_command(test_device_id, command_payload_1),
                api_command(test_device_id, command_payload_2),
                api_command(test_device_id, command_payload_3),
            )
            time.sleep(0.5)
            # only a single response is received, but all commands are published
            self.ec.post(command_response("id", CmdResponseType.OK, 2), sleep=0.2)
            msgs = [MessageToDict(_ExternalServerMsg.FromString(r.payload)) for r in f1.result()]
            self.assertEqual(msgs[0]["command"]["messageCounter"], 1)
            self.assertEqual(msgs[1]["command"]["messageCounter"], 2)
            self.assertEqual(msgs[2]["command"]["messageCounter"], 3)

    def tearDown(self) -> None:
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_sequence(self, car_name: str):
        self.ec.post(connect_msg("id", "company_x", car_name, [test_device]), sleep=0.1)
        self.ec.post(
            status("id", "CONNECTING", test_device, 0, {"content": "test", "timestamp": 000})
        )
        self.ec.post(command_response("id", CmdResponseType.OK, 0))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
