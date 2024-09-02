import unittest
import sys
import subprocess
import time

sys.path.append(".")

from tests.broker import MQTTBrokerTest
from tests.utils import (
    Action,
    AutonomyState,
    AutonomyStatus,
    ApiClientTest,
    CmdResponseType,
    DeviceState,
    ExternalClientMock,
    api_command,
    api_status,
    command_response,
    connect_msg,
    device_id,
    device_obj,
    status,
    station,
    position,
    run_from_docker_compose,
)


autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, type=1, role="driving", name="Autonomy")
API_HOST = "http://localhost:8080/v2/protocol"


class Test_Connection_Sequence(unittest.TestCase):

    def setUp(self) -> None:
        self.broker = MQTTBrokerTest(start=True)
        self.ec = ExternalClientMock(self.broker, "company_x", "car_a")
        self.api_client = ApiClientTest(API_HOST, "company_x", "car_a", "TestAPIKey")
        run_from_docker_compose()
        time.sleep(1)
        self.payload = AutonomyStatus().SerializeToString()

    def test_sending_connect_message_statuses_and_commands_makes_successful_connect_sequence(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0), sleep=0.5)
        s = self.api_client.get_statuses()[0]
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
        statuses = self.api_client.get_statuses(wait=True)
        self.assertEqual(len(statuses), 0)

    def test_sending_status_twice_stops_the_sequence_and_prevents_sending_of_command_via_mqtt(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        s = self.api_client.get_statuses(wait=True)[0]
        self.assertEqual(s.device_id.module_id, autonomy.module)
        self.assertEqual(s.device_id.type, autonomy.deviceType)
        self.assertEqual(s.device_id.role, autonomy.deviceRole)
        self.assertEqual(s.device_id.name, autonomy.deviceName)
        self.assertEqual(s.payload.data.to_dict()["state"], "IDLE")

    def test_sending_getting_multiple_commands_does_not_interrupt_the_connect_sequence(self):
        self.api_client.post_statuses(
            api_status(
                device_id=autonomy_id,
                state=AutonomyState.DRIVE,
                telemetry=AutonomyStatus.Telemetry(
                    speed=0.0, fuel=0.85, position=position(49.0, 16.0, 123.4)
                ),
                next_stop=station("stop_a", position(49.1, 16.0, 123.4)),
            )
        )
        time.sleep(1)
        statuses = self.api_client.get_statuses()
        self.assertEqual(len(statuses), 1)
        self.api_client.post_commands(
            api_command(
                device_id=autonomy_id,
                action=Action.START,
                stops=[station("stop_a", position(49.1, 16.0, 123.4))],
                route="route_1",
            ),
            api_command(
                device_id=autonomy_id,
                action=Action.START,
                stops=[
                    station("stop_a", position(49.1, 16.0, 123.4)),
                    station("stop_b", position(49.2, 16.01, 129.4)),
                ],
                route="route_1",
            ),
        )
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.2)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        time.sleep(1)
        statuses = self.api_client.get_statuses()
        self.assertEqual(statuses[-1].device_id.module_id, autonomy.module)
        self.assertEqual(statuses[-1].device_id.type, autonomy.deviceType)
        self.assertEqual(statuses[-1].device_id.role, autonomy.deviceRole)
        self.assertEqual(statuses[-1].device_id.name, autonomy.deviceName)
        self.assertEqual(statuses[-1].payload.message_type, "STATUS")
        self.assertEqual(statuses[-1].payload.encoding, "JSON")
        self.assertEqual(len(statuses), 2)

    def tearDown(self):
        subprocess.run(["docker", "compose", "down"])
        self.broker.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
