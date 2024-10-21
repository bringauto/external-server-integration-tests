import unittest
import time
from concurrent import futures

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    api_command,
    command_response,
    connect_msg,
    device_obj,
    CmdResponseType,
    Device,
    device_id,
    status,
)
from ExternalProtocol_pb2 import ExternalServer as ExternalServerMsg  # type: ignore


API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()
test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
unsupported_device = device_obj(
    module_id=1,
    device_type=123456789,
    role="notdriving",
    name="UnsupportedDevice",
    priority=0,
)


class Test_Succesfull_Communication_With_Single_Device(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(test_device=test_device, ext_client=self.ec)

    def test_status_sent_after_successful_connect_sequence_from_device_is_available_on_api(
        self,
    ):
        # send status message
        status_payload = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(status("id", "RUNNING", test_device, 1, status_payload))
        statuses = self.api_client.get_statuses("company_x", "car_a", wait=True)
        self.assertEqual(statuses[-1].payload.data.to_dict(), status_payload)

    def test_command_posted_on_api_after_connect_sequence_is_forwarded_to_device(self):
        cmd_payload = {"content": "An arbitrary command ...", "timestamp": 222}
        with futures.ThreadPoolExecutor() as ex:
            f = ex.submit(self.ec.get, n=1)
            self.api_client.post_commands(
                "company_x", "car_a", api_command(test_device_id, cmd_payload)
            )
            msg = f.result(timeout=5)[0]
            msg = ExternalServerMsg.FromString(msg.payload)
            self.assertEqual(msg.command.deviceCommand.device.deviceName, "Test_Device_1")
            self.assertEqual(msg.command.deviceCommand.device.deviceRole, "test_device_1")

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_sequence(self, test_device: Device, ext_client: ExternalClientMock) -> None:
        status_payload = {"content": "An arbitrary string ...", "timestamp": 000}
        ext_client.post(connect_msg("id", "company_x", "car_a", [test_device]))
        ext_client.post(status("id", "CONNECTING", test_device, 0, status_payload))
        ext_client.post(command_response("id", CmdResponseType.OK, 0))


class Test_Messages_From_Unsupported_Device(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(test_device=test_device, ext_client=self.ec)

    def test_messages_from_unsupp_device_are_ignored_and_not_sent_to_api(self):
        timestamp = int(time.time() * 1000)
        payload_1 = {"content": "An arbitrary string ...", "timestamp": 111}
        payload_2 = {"content": "An arbitrary string ...", "timestamp": 222}
        self.ec.post(status("id", "RUNNING", test_device, 1, payload_1))
        self.ec.post(status("id", "CONNECTING", unsupported_device, 2, payload_2))
        s = self.api_client.get_statuses("company_x", "car_a", since=timestamp, wait=True)
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0].device_id.module_id, test_device.module)
        self.assertEqual(s[0].device_id.name, "Test_Device_1")
        self.assertEqual(s[0].device_id.role, "test_device_1")
        self.assertEqual(s[0].payload.data.to_dict(), payload_1)

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_sequence(self, test_device: Device, ext_client: ExternalClientMock) -> None:
        status_payload = {"content": "An arbitrary string ...", "timestamp": 000}
        ext_client.post(connect_msg("id", "company_x", "car_a", [test_device]))
        ext_client.post(status("id", "CONNECTING", test_device, 0, status_payload))
        ext_client.post(command_response("id", CmdResponseType.OK, 0))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
