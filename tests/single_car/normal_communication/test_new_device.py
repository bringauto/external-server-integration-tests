import unittest
import time
import json

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    command_response,
    connect_msg,
    device_obj,
    CmdResponseType,
    Device,
    device_id,
    status,
)


API_HOST = "http://localhost:8080/v2/protocol"


test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
button = device_obj(module_id=2, device_type=3, role="button", name="Button", priority=0)
button_id = device_id(module_id=2, device_type=3, role="button", name="Button")


_comm_layer = communication_layer()


class Test_New_Supported_Device_Connecting_After_Connect_Sequence(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(test_device=test_device, ext_client=self.ec)

    def test_connecting_status_sent_after_successful_connect_sequence_from_device_is_available_on_api(
        self,
    ):
        payload = {"data": [[], [], {"butPr": 0}]}
        connect_status = status(
            session_id="session_id",
            state="CONNECTING",
            device=button,
            counter=1,
            payload=json.dumps(payload).encode(),
        )
        self.ec.post(connect_status)
        statuses = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(len(statuses), 2)
        self.assertEqual(statuses[0].device_id, test_device_id)
        self.assertEqual(statuses[1].device_id, button_id)

    def test_running_status_sent_without_device_being_connected_is_not_available_on_api(
        self,
    ):
        payload = {"data": [[], [], {"butPr": 0}]}
        running_status = status(
            session_id="session_id",
            state="RUNNING",
            device=button,
            counter=1,
            payload=json.dumps(payload).encode(),
        )
        self.ec.post(running_status)
        statuses = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(len(statuses), 1)

    def test_running_status_after_connecting_status_becomes_available_on_api(self):
        payload = {"data": [[], [], {"butPr": 0}]}
        connect_status = status(
            session_id="session_id",
            state="CONNECTING",
            device=button,
            counter=1,
            payload=json.dumps(payload).encode(),
        )
        running_status = status(
            session_id="session_id",
            state="RUNNING",
            device=button,
            counter=2,
            payload=json.dumps(payload).encode(),
        )
        self.ec.post(connect_status)
        self.ec.post(running_status)
        statuses = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(len(statuses), 3)

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_sequence(self, test_device: Device, ext_client: ExternalClientMock) -> None:
        ext_client.post(connect_msg("session_id", "company_x", "car_a", [test_device]))
        payload = {"content": "test", "timestamp": 000}
        ext_client.post(status("session_id", "CONNECTING", test_device, 0, payload))
        ext_client.post(command_response("session_id", CmdResponseType.OK, 0))


# the device type is not supported by module 2
unsupported_button = device_obj(
    module_id=2, device_type=1111, role="button", name="Button", priority=0
)


class Test_New_Unsupported_Device_Connecting_After_Connect_Sequence(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(test_device=test_device, ext_client=self.ec)
        time.sleep(1)

    def test_connecting_status_sent_after_successful_connect_sequence_is_not_available_on_api(
        self,
    ):
        payload = {"data": [[], [], {"butPr": 0}]}
        connect_status = status(
            session_id="session_id",
            state="CONNECTING",
            device=unsupported_button,
            counter=1,
            payload=json.dumps(payload).encode(),
        )
        self.ec.post(connect_status)
        statuses = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0].device_id, test_device_id)

    def test_running_status_sent_after_successful_connect_sequence_is_not_available_on_api(
        self,
    ):
        payload = {"data": [[], [], {"butPr": 0}]}
        connect_status = status(
            session_id="session_id",
            state="RUNNING",
            device=unsupported_button,
            counter=1,
            payload=json.dumps(payload).encode(),
        )
        self.ec.post(connect_status)
        statuses = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0].device_id, test_device_id)

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_sequence(self, test_device: Device, ext_client: ExternalClientMock) -> None:
        ext_client.post(connect_msg("session_id", "company_x", "car_a", [test_device]))
        payload = {"content": "test", "timestamp": 000}
        ext_client.post(status("session_id", "CONNECTING", test_device, 0, payload))
        ext_client.post(command_response("session_id", CmdResponseType.OK, 0))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
