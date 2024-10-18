import unittest
import json
import time
from concurrent import futures

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    api_command,
    api_status,
    command_response,
    connect_msg,
    device_obj,
    device_id,
    CmdResponseType,
    status,
)


API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()
test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")


class Test_New_Connection_Sequence_Is_Accepted_After_Mqtt_Timeout(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()

    def test_new_connection_seq_is_accepted_if_no_status_is_sent_from_ext_client(self):
        payload_1 = {"content": "An arbitrary string ...", "timestamp": 111}
        payload_2 = {"content": "An arbitrary string XXX", "timestamp": 222}
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]))
        self.ec.post(status("id", "CONNECTING", test_device, 0, payload_1))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        mqtt_timeout = json.load(open("config/external-server/config.json"))["mqtt_timeout"]
        time.sleep(mqtt_timeout + 1)
        self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]))
        self.ec.post(status("id", "CONNECTING", test_device, 0, payload_2))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        s = self.api_client.get_statuses("company_x", "car_a", wait=True)
        self.assertEqual(len(s), 2)

    def test_commands_not_send_during_external_connection_outage_are_sent_after_reconnection(self):
        with futures.ThreadPoolExecutor() as ex:
            # the connection is now not established
            status_payload_1 = {"content": "An arbitrary status ...", "timestamp": 000}
            command_payload_1 = {"content": "An arbitrary command ...", "timestamp": 111}
            command_payload_2 = {"content": "An arbitrary command ...", "timestamp": 222}
            status_payload_2 = {"content": "An arbitrary status ...", "timestamp": 333}

            self.api_client.post_statuses(
                "company_x", "car_a", api_status(test_device_id, status_payload_1)
            )
            self.api_client.post_commands(
                "company_x", "car_a", api_command(test_device_id, command_payload_1)
            )
            self.api_client.post_commands(
                "company_x", "car_a", api_command(test_device_id, command_payload_2)
            )
            # reconnection
            self.ec.post(connect_msg("id", "company_x", "car_a", [test_device]))
            f = ex.submit(self.ec.get, 2)
            self.ec.post(status("id", "CONNECTING", test_device, 0, status_payload_2))
            self.ec.post(command_response("id", CmdResponseType.OK, 0))
            messages = f.result(timeout=5)
            self.assertEqual(len(messages), 2)

    def tearDown(self) -> None:
        docker_compose_down()
        _comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
