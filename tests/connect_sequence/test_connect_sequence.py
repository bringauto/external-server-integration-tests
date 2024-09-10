import unittest
import sys
import time

sys.path.append(".")

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.misc import clear_logs
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


autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, type=1, role="driving", name="Autonomy")
API_HOST = "http://localhost:8080/v2/protocol"
comm_layer = communication_layer()


class Test_Connection_Sequence(unittest.TestCase):

    def setUp(self) -> None:
        clear_logs()
        comm_layer.start()
        self.ec = ExternalClientMock(comm_layer, "company_x", "car_a")
        self.api = ApiClientMock(API_HOST, "company_x", "car_a", "TestAPIKey")
        docker_compose_up()
        self.payload = AutonomyStatus().SerializeToString()

    def test_sending_connect_message_statuses_and_commands_makes_successful_connect_sequence(
        self,
    ):
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0), sleep=0.5)
        s = self.api.get_statuses()[0]
        self.assertEqual(s.device_id.module_id, autonomy.module)
        self.assertEqual(s.device_id.type, autonomy.deviceType)
        self.assertEqual(s.device_id.role, autonomy.deviceRole)
        self.assertEqual(s.device_id.name, autonomy.deviceName)
        self.assertEqual(s.payload.message_type, "STATUS")
        self.assertEqual(s.payload.encoding, "JSON")
        self.assertEqual(s.payload.data.to_dict()["state"], "IDLE")

    def test_sending_connect_msg_twice_stops_sequence_and_prevents_sending_status(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        time.sleep(0.5)
        statuses = self.api.get_statuses(wait=True)
        self.assertEqual(len(statuses), 0)

    def test_sending_status_twice_stops_the_sequence_and_prevents_sending_of_command_via_mqtt(
        self,
    ):
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        s = self.api.get_statuses(wait=True)[0]
        self.assertEqual(s.device_id.module_id, autonomy.module)
        self.assertEqual(s.device_id.type, autonomy.deviceType)
        self.assertEqual(s.device_id.role, autonomy.deviceRole)
        self.assertEqual(s.device_id.name, autonomy.deviceName)
        self.assertEqual(s.payload.data.to_dict()["state"], "IDLE")

    def test_sending_getting_multiple_commands_does_not_interrupt_the_connect_sequence(
        self,
    ):
        stop_a = station("stop_a", position(49.1, 16.0, 123.4))
        stop_b = station("stop_b", position(49.2, 16.01, 129.4))
        telemetry = AutonomyStatus.Telemetry(
            speed=0.0, fuel=0.85, position=position(49.0, 16.0, 123.4)
        )
        self.api.post_statuses(api_status(autonomy_id, AutonomyState.DRIVE, telemetry, stop_b))
        time.sleep(0.5)
        statuses = self.api.get_statuses()
        self.api.post_commands(
            api_command(autonomy_id, Action.START, [stop_a], "route_1"),
            api_command(autonomy_id, Action.START, [stop_a, stop_b], "route_1"),
        )
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.2)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        time.sleep(0.5)
        statuses = self.api.get_statuses()
        self.assertEqual(statuses[-1].device_id.module_id, autonomy.module)
        self.assertEqual(statuses[-1].device_id.type, autonomy.deviceType)
        self.assertEqual(statuses[-1].device_id.role, autonomy.deviceRole)
        self.assertEqual(statuses[-1].device_id.name, autonomy.deviceName)
        self.assertEqual(statuses[-1].payload.message_type, "STATUS")
        self.assertEqual(statuses[-1].payload.encoding, "JSON")
        self.assertEqual(len(statuses), 2)

    def tearDown(self):
        docker_compose_down()
        comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
