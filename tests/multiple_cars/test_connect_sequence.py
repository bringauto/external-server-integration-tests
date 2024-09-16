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
        self.ec_1 = ExternalClientMock(comm_layer, "company_x", "car_1")
        self.ec_2 = ExternalClientMock(comm_layer, "company_x", "car_2")
        self.api_1 = ApiClientMock(API_HOST, "company_x", "car_1", "TestAPIKey")
        self.api_2 = ApiClientMock(API_HOST, "company_x", "car_2", "TestAPIKey")
        docker_compose_up("config_2_cars.json")
        self.payload = AutonomyStatus().SerializeToString()

    def test_sending_connect_message_statuses_and_commands_makes_successful_connect_sequence(
        self,
    ):
        self.ec_1.post(connect_msg("id", "company_x", "car_1", [autonomy]), sleep=0.1)
        self.ec_1.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec_1.post(command_response("id", CmdResponseType.OK, 0))

        self.ec_2.post(connect_msg("id", "company_x", "car_2", [autonomy]), sleep=0.1)
        self.ec_2.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec_2.post(command_response("id", CmdResponseType.OK, 0))

        time.sleep(0.5)

        s_1 = self.api_1.get_statuses()[0]
        self.assertEqual(s_1.device_id.module_id, autonomy.module)
        self.assertEqual(s_1.device_id.type, autonomy.deviceType)
        self.assertEqual(s_1.device_id.role, autonomy.deviceRole)
        self.assertEqual(s_1.device_id.name, autonomy.deviceName)
        self.assertEqual(s_1.payload.message_type, "STATUS")
        self.assertEqual(s_1.payload.encoding, "JSON")
        self.assertEqual(s_1.payload.data.to_dict()["state"], "IDLE")

        s_2 = self.api_2.get_statuses()[0]
        self.assertEqual(s_2.device_id.module_id, autonomy.module)
        self.assertEqual(s_2.device_id.type, autonomy.deviceType)
        self.assertEqual(s_2.device_id.role, autonomy.deviceRole)
        self.assertEqual(s_2.device_id.name, autonomy.deviceName)
        self.assertEqual(s_2.payload.message_type, "STATUS")
        self.assertEqual(s_2.payload.encoding, "JSON")
        self.assertEqual(s_2.payload.data.to_dict()["state"], "IDLE")

    def test_one_failing_connect_sequence_does_not_affect_other_car_connect_sequence(self):
        # connect sequence runs only for car_1
        self.ec_1.post(connect_msg("id", "company_x", "car_1", [autonomy]), sleep=0.1)
        self.ec_1.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec_1.post(command_response("id", CmdResponseType.OK, 0))

        time.sleep(0.5)

        self.ec_1.post(status("id", DeviceState.RUNNING, autonomy, 0, self.payload), sleep=0.1)
        self.ec_2.post(status("id", DeviceState.RUNNING, autonomy, 0, self.payload), sleep=0.1)

        time.sleep(0.5)

        # status for car_1 has been succesfully sent
        statuses = self.api_1.get_statuses()
        self.assertEqual(len(statuses), 2)
        # no status for car_2 - connect sequence failed
        statuses = self.api_2.get_statuses()
        self.assertEqual(len(statuses), 0)

    def tearDown(self):
        docker_compose_down()
        comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
