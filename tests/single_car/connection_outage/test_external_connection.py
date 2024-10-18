import unittest
import json
import time
from concurrent import futures

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    Action,
    AutonomyStatus,
    telemetry,
    api_autonomy_status,
    command_response,
    connect_msg,
    device_obj,
    device_id,
    CmdResponseType,
    DeviceState,
    status,
    api_autonomy_command,
)


API_HOST = "http://localhost:8080/v2/protocol"
_comm_layer = communication_layer()
autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, type=1, role="driving", name="Autonomy")


class Test_New_Connection_Sequence_Is_Accepted_After_Mqtt_Timeout(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self.payload = AutonomyStatus().SerializeToString()

    def test_new_connection_seq_is_accepted_if_no_status_is_sent_from_ext_client_for_long_time(
        self,
    ):
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.2)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        mqtt_timeout = json.load(open("config/external-server/config.json"))["mqtt_timeout"]
        time.sleep(mqtt_timeout + 2)
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.2)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        time.sleep(1)
        s = self.api_client.get_statuses("company_x", "car_a")
        self.assertEqual(len(s), 2)

    def test_commands_not_send_during_external_connection_outage_are_sent_after_reconnection(self):
        with futures.ThreadPoolExecutor() as ex:
            # the connection is now not established
            command_1 = api_autonomy_command(autonomy_id, Action.NO_ACTION, [], "")
            command_2 = api_autonomy_command(autonomy_id, Action.START, [], "route_1")
            self.api_client.post_statuses(
                "company_x",
                "car_a",
                api_autonomy_status(autonomy_id, AutonomyStatus.IDLE, telemetry=telemetry()),
            )
            self.api_client.post_commands("company_x", "car_a", command_1)
            self.api_client.post_commands("company_x", "car_a", command_2)

            # reconnection
            self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.2)

            f = ex.submit(self.ec.get, 2)

            self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
            self.ec.post(command_response("id", CmdResponseType.OK, 0))

            messages = f.result()
            self.assertEqual(len(messages), 2)

    def tearDown(self) -> None:
        docker_compose_down()
        _comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
