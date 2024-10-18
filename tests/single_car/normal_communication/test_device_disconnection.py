import unittest
import time
import json

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    connect_msg,
    command_response,
    device_obj,
    DeviceState,
    DeviceId,
    status,
    CmdResponseType,
)


API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()
button_1 = device_obj(module_id=2, type=3, role="button_1", name="Button1", priority=0)
button_1_id = DeviceId(module_id=2, type=3, role="button_1", name="Button1")
button_2 = device_obj(module_id=2, type=3, role="button_2", name="Button2", priority=0)


class Test_Device_Disconnection(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()

    def test_statuses_of_disconnected_device_are_not_forwarded_to_api(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [button_1, button_2]))
        payload_dict = {"data": [[], [], {"butPr": 0}]}
        payload = json.dumps(payload_dict).encode()
        self.ec.post(status("id", DeviceState.CONNECTING, button_1, 0, payload))
        self.ec.post(status("id", DeviceState.CONNECTING, button_2, 1, payload))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))

        time.sleep(0.1)
        self.ec.post(status("id", DeviceState.DISCONNECT, button_1, 2, payload))

        time.sleep(0.1)
        timestamp = int(1000 * time.time())

        self.ec.post(status("id", DeviceState.RUNNING, button_2, 3, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_1, 4, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_2, 5, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_1, 6, payload))

        time.sleep(0.1)
        statuses = self.api_client.get_statuses("company_x", "car_a", since=timestamp)
        # the status from button_1 is not present in the list of statuses
        self.assertEqual(len(statuses), 2)
        self.assertNotIn(button_1_id, [status.device_id for status in statuses])

    def test_statuses_of_connected_device_are_again_forwarded_to_api(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [button_1, button_2]))
        payload_dict = {"data": [[], [], {"butPr": 0}]}
        payload = json.dumps(payload_dict).encode()
        self.ec.post(status("id", DeviceState.CONNECTING, button_1, 0, payload))
        self.ec.post(status("id", DeviceState.CONNECTING, button_2, 1, payload))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))

        time.sleep(0.1)
        self.ec.post(status("id", DeviceState.DISCONNECT, button_1, 2, payload))

        time.sleep(0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, button_1, 3, payload))

        time.sleep(0.1)
        self.ec.post(status("id", DeviceState.RUNNING, button_2, 4, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_1, 5, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_2, 6, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_1, 7, payload))

    def test_connection_sequence_is_repeated_if_all_devices_disconnect(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [button_1, button_2]))
        payload_dict = {"data": [[], [], {"butPr": 0}]}
        payload = json.dumps(payload_dict).encode()
        self.ec.post(status("id", DeviceState.CONNECTING, button_1, 0, payload))
        self.ec.post(status("id", DeviceState.CONNECTING, button_2, 1, payload))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))

        time.sleep(0.5)
        self.ec.post(status("id", DeviceState.DISCONNECT, button_1, 2, payload))
        self.ec.post(status("id", DeviceState.DISCONNECT, button_2, 3, payload))

        time.sleep(2)
        self.ec.post(connect_msg("new_id", "company_x", "car_a", [button_1, button_2]), sleep=0.1)
        payload_dict = {"data": [[], [], {"butPr": 0}]}
        payload = json.dumps(payload_dict).encode()
        self.ec.post(status("new_id", DeviceState.CONNECTING, button_1, 2, payload), sleep=0.1)
        self.ec.post(status("new_id", DeviceState.CONNECTING, button_2, 3, payload), sleep=0.1)
        self.ec.post(command_response("new_id", CmdResponseType.OK, 2), sleep=0.1)
        self.ec.post(command_response("new_id", CmdResponseType.OK, 3), sleep=0.1)

        time.sleep(0.5)
        timestamp = int(1000 * time.time())
        payload = json.dumps({"data": [[], [], {"butPr": 1}]}).encode()
        self.ec.post(status("new_id", DeviceState.RUNNING, button_1, 4, payload), sleep=0.1)

        statuses = self.api_client.get_statuses("company_x", "car_a", since=timestamp)
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0].payload.data.to_dict()["data"][2]["butPr"], 1)

    def test_device_is_disconnected_immediatelly_after_receving_command_response_even_though_not_in_order(
        self,
    ):
        self.ec.post(connect_msg("id", "company_x", "car_a", [button_1, button_2]))
        payload_dict = {"data": [[], [], {"butPr": 0}]}
        payload = json.dumps(payload_dict).encode()
        self.ec.post(status("id", DeviceState.CONNECTING, button_1, 0, payload))
        self.ec.post(status("id", DeviceState.CONNECTING, button_2, 1, payload))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))

    def tearDown(self) -> None:
        docker_compose_down()
        _comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
