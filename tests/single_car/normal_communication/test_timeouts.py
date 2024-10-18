import unittest
import sys
import time
import json

sys.path.append("lib/fleet-protocol/protobuf/compiled/python")

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    Action,
    api_autonomy_command,
    command_response,
    connect_msg,
    device_obj,
    CmdResponseType,
    AutonomyStatus,
    Device,
    device_id,
    DeviceState,
    status,
)


autonomy = device_obj(module_id=1, device_type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, device_type=1, role="driving", name="Autonomy")
API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()


class Test_Message_Timeout(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(session_id="id", autonomy=autonomy, ext_client=self.ec)
        self.msg_timeout = json.load(open("config/external-server/config.json"))["timeout"]

    def test_not_receiving_skipped_status_until_timeout_allows_for_new_connect_sequence_with_new_session_id(
        self,
    ):
        payload = AutonomyStatus().SerializeToString()
        self.ec.post(status("id", DeviceState.RUNNING, autonomy, 1, payload), sleep=0.1)
        self.ec.post(status("id", DeviceState.RUNNING, autonomy, 3, payload), sleep=0.1)
        time.sleep(self.msg_timeout)
        # timeout is reached, new connection sequence below is accepted
        time.sleep(1)
        self._run_connect_sequence(session_id="new_id", autonomy=autonomy, ext_client=self.ec)
        timestamp = int(time.time() * 1000)
        payload = AutonomyStatus().SerializeToString()
        # status is published with new session id and forwared to the API
        self.ec.post(status("new_id", DeviceState.RUNNING, autonomy, 1, payload), sleep=0.1)
        time.sleep(0.5)
        s = self.api_client.get_statuses("company_x", "car_a", since=timestamp)
        self.assertEqual(len(s), 1)

    def test_not_receiving_cmd_response_allows_for_new_connect_seq_with_new_session_id(
        self,
    ):
        payload = AutonomyStatus().SerializeToString()
        self.api_client.post_commands(
            "company_x", "car_a", api_autonomy_command(autonomy_id, Action.NO_ACTION, [], "")
        )
        time.sleep(self.msg_timeout / 2)
        self.ec.post(status("id", DeviceState.RUNNING, autonomy, 1, payload), sleep=0.1)
        time.sleep(self.msg_timeout / 2)
        # timeout is reached, new connection sequence below is accepted
        time.sleep(1)
        self._run_connect_sequence(session_id="new_id", autonomy=autonomy, ext_client=self.ec)
        timestamp = int(time.time() * 1000)
        # status is published with new session id and forwared to the API
        self.ec.post(status("new_id", DeviceState.RUNNING, autonomy, 1, payload), sleep=0.1)
        time.sleep(0.5)
        s = self.api_client.get_statuses("company_x", "car_a", since=timestamp)
        self.assertEqual(len(s), 1)

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_sequence(
        self, session_id: str, autonomy: Device, ext_client: ExternalClientMock
    ) -> None:
        ext_client.post(connect_msg(session_id, "company_x", "car_a", [autonomy]), sleep=0.1)
        payload = AutonomyStatus().SerializeToString()
        ext_client.post(status(session_id, DeviceState.CONNECTING, autonomy, 0, payload), sleep=0.1)
        ext_client.post(command_response(session_id, CmdResponseType.OK, 0), sleep=0.5)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
