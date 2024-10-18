import unittest
import time
import json

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
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
    position,
)


API_HOST = "http://localhost:8080/v2/protocol"
comm_layer = communication_layer()
test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")


class Test_Connection_Sequence(unittest.TestCase):

    def setUp(self) -> None:
        comm_layer.start()
        self.ec = ExternalClientMock(comm_layer, "company_x", "car_a")
        self.api = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()

    def test_sending_connect_message_statuses_and_commands_makes_successful_connect_sequence(
        self,
    ):
        payload = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]), sleep=0.1)
        self.ec.post(
            status("id", DeviceState.CONNECTING, test_device, 0, json.dumps(payload).encode()),
            sleep=0.1,
        )
        self.ec.post(command_response("id", CmdResponseType.OK, 0), sleep=0.5)
        statuses = self.api.get_statuses("company_x", "car_a")
        self.assertEqual(len(statuses), 1)
        s = statuses[0]
        self.assertEqual(s.device_id.module_id, test_device.module)
        self.assertEqual(s.device_id.name, test_device.deviceName)
        self.assertEqual(s.payload.data.to_dict(), payload)

    def test_sending_connect_msg_twice_stops_sequence_and_prevents_sending_status(self):
        payload = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]), sleep=0.1)
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]), sleep=0.1)
        self.ec.post(
            status("id", DeviceState.CONNECTING, test_device, 0, json.dumps(payload).encode()),
            sleep=0.1,
        )
        time.sleep(0.5)
        statuses = self.api.get_statuses("company_x", "car_a", wait=True)
        self.assertEqual(len(statuses), 0)

    def test_sending_status_twice_stops_the_sequence_and_prevents_sending_of_command_via_mqtt(
        self,
    ):
        payload = {"content": "An arbitrary string ...", "timestamp": 111}
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]), sleep=0.1)
        self.ec.post(
            status("id", DeviceState.CONNECTING, test_device, 0, json.dumps(payload).encode()),
            sleep=0.1,
        )
        self.ec.post(
            status("id", DeviceState.CONNECTING, test_device, 0, json.dumps(payload).encode()),
            sleep=0.1,
        )
        s = self.api.get_statuses("company_x", "car_a", wait=True)[0]
        self.assertEqual(s.device_id.module_id, test_device.module)
        self.assertEqual(s.device_id.type, test_device.deviceType)
        self.assertEqual(s.device_id.role, test_device.deviceRole)
        self.assertEqual(s.device_id.name, test_device.deviceName)
        self.assertEqual(s.payload.data.to_dict(), payload)

    def test_sending_getting_multiple_commands_does_not_interrupt_the_connect_sequence(
        self,
    ):
        status_payload = {"content": "An arbitrary string ...", "timestamp": 111}
        command_payload_1 = {"content": "Another arbitrary string 🌲", "timestamp": 222}
        command_payload_2 = {"content": "Yet another arbitrary string 🌲🌲", "timestamp": 333}
        self.api.post_statuses(
            "company_x",
            "car_a",
            api_status(test_device_id, status_payload),
        )
        self.api.post_commands(
            "company_x",
            "car_a",
            api_command(test_device_id, command_payload_1),
            api_command(test_device_id, command_payload_2),
        )
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]), sleep=0.1)
        self.ec.post(
            status(
                "id", DeviceState.CONNECTING, test_device, 0, json.dumps(status_payload).encode()
            ),
            sleep=0.1,
        )
        self.ec.post(command_response("id", CmdResponseType.OK, 0), sleep=0.5)
        statuses = self.api.get_statuses("company_x", "car_a")
        self.assertEqual(len(statuses), 2)

    def tearDown(self):
        docker_compose_down()
        comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
