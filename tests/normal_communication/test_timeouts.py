import unittest
import sys
import time
import json

sys.path.append(".")

from tests._utils.misc import clear_logs
from tests._utils.broker import MQTTBrokerTest
from tests._utils.mocks import (
    ApiClientTest,
    ExternalClientMock,
    docker_compose_up,
    docker_compose_down,
)
from tests._utils.messages import (
    Action,
    api_command,
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


autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, type=1, role="driving", name="Autonomy")
API_HOST = "http://localhost:8080/v2/protocol"


_broker = MQTTBrokerTest()


class Test_Message_Timeout(unittest.TestCase):

    def setUp(self) -> None:
        clear_logs()
        self.broker = _broker
        self.broker.start()
        self.ec = ExternalClientMock(self.broker, "company_x", "car_a")
        self.api_client = ApiClientTest(API_HOST, "company_x", "car_a", "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(session_id="id", autonomy=autonomy, ext_client=self.ec)
        self.msg_timeout = json.load(open("config/external-server/config.json"))["timeout"]

    def test_not_receiving_skipped_status_until_timeout_allows_for_new_connect_sequence_with_new_session_id(
        self,
    ):
        self.ec.post(
            status("id", DeviceState.RUNNING, autonomy, 1, AutonomyStatus().SerializeToString()),
            sleep=0.1,
        )
        self.ec.post(
            status("id", DeviceState.RUNNING, autonomy, 3, AutonomyStatus().SerializeToString()),
            sleep=0.1,
        )
        time.sleep(self.msg_timeout)
        # timeout is reached, new connection sequence below is accepted
        time.sleep(
            1
        )  # sleep to let the server clear its context and prepare for new connection sequence
        self._run_connect_sequence(session_id="new_id", autonomy=autonomy, ext_client=self.ec)
        timestamp = int(time.time() * 1000)
        # status is published with new session id and forwared to the API
        self.ec.post(
            status(
                "new_id", DeviceState.RUNNING, autonomy, 1, AutonomyStatus().SerializeToString()
            ),
            sleep=0.1,
        )
        time.sleep(0.5)
        s = self.api_client.get_statuses(since=timestamp)
        self.assertEqual(len(s), 1)

    def test_not_receiving_command_response_until_timeout_allows_for_new_connect_sequence_with_new_session_id(
        self,
    ):
        self.api_client.post_commands(api_command(autonomy_id, Action.NO_ACTION, [], ""))
        time.sleep(self.msg_timeout / 2)
        self.ec.post(
            status("id", DeviceState.RUNNING, autonomy, 1, AutonomyStatus().SerializeToString()),
            sleep=0.1,
        )
        time.sleep(self.msg_timeout / 2)
        # timeout is reached, new connection sequence below is accepted
        time.sleep(
            1
        )  # sleep to let the server clear its context and prepare for new connection sequence
        self._run_connect_sequence(session_id="new_id", autonomy=autonomy, ext_client=self.ec)
        timestamp = int(time.time() * 1000)
        # status is published with new session id and forwared to the API
        self.ec.post(
            status(
                "new_id", DeviceState.RUNNING, autonomy, 1, AutonomyStatus().SerializeToString()
            ),
            sleep=0.1,
        )
        time.sleep(0.5)
        s = self.api_client.get_statuses(since=timestamp)
        self.assertEqual(len(s), 1)

    def tearDown(self):
        docker_compose_down()

    def _run_connect_sequence(
        self, session_id: str, autonomy: Device, ext_client: ExternalClientMock
    ) -> None:
        ext_client.post(connect_msg(session_id, "company_x", "car_a", [autonomy]), sleep=0.1)
        empty_status = AutonomyStatus().SerializeToString()
        ext_client.post(
            status(session_id, DeviceState.CONNECTING, autonomy, 0, empty_status), sleep=0.1
        )
        ext_client.post(command_response(session_id, CmdResponseType.OK, 0), sleep=0.5)


if __name__ == "__main__":  # pragma: no cover
    _broker.start()
    unittest.main()
    _broker.stop()
