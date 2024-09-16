import unittest
import sys
import time

sys.path.append(".")

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.misc import clear_logs
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    AutonomyStatus,
    CmdResponseType,
    DeviceState,
    command_response,
    connect_msg,
    device_id,
    device_obj,
    status
)


autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, type=1, role="driving", name="Autonomy")
API_HOST = "http://localhost:8080/v2/protocol"
comm_layer = communication_layer()


class Test_Connection_Sequence(unittest.TestCase):

    def setUp(self) -> None:
        clear_logs()
        comm_layer.start()
        self.ec_a = ExternalClientMock(comm_layer, "company_x", "car_a")
        self.ec_b = ExternalClientMock(comm_layer, "company_x", "car_b")
        self.api = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up("config_2_cars.json")
        self.payload = AutonomyStatus().SerializeToString()

    def test_sending_connect_message_statuses_and_commands_makes_successful_connect_sequence(
        self,
    ):
        self.ec_a.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        self.ec_a.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec_a.post(command_response("id", CmdResponseType.OK, 0))

        self.ec_b.post(connect_msg("id", "company_x", "car_b", [autonomy]), sleep=0.1)
        self.ec_b.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec_b.post(command_response("id", CmdResponseType.OK, 0))

        time.sleep(0.5)

        s_a = self.api.get_statuses("company_x", "car_a")[0]
        self.assertEqual(s_a.device_id.module_id, autonomy.module)
        self.assertEqual(s_a.device_id.type, autonomy.deviceType)
        self.assertEqual(s_a.device_id.role, autonomy.deviceRole)
        self.assertEqual(s_a.device_id.name, autonomy.deviceName)
        self.assertEqual(s_a.payload.message_type, "STATUS")
        self.assertEqual(s_a.payload.encoding, "JSON")
        self.assertEqual(s_a.payload.data.to_dict()["state"], "IDLE")

        s_b = self.api.get_statuses("company_x", "car_b")[0]
        self.assertEqual(s_b.device_id.module_id, autonomy.module)
        self.assertEqual(s_b.device_id.type, autonomy.deviceType)
        self.assertEqual(s_b.device_id.role, autonomy.deviceRole)
        self.assertEqual(s_b.device_id.name, autonomy.deviceName)
        self.assertEqual(s_b.payload.message_type, "STATUS")
        self.assertEqual(s_b.payload.encoding, "JSON")
        self.assertEqual(s_b.payload.data.to_dict()["state"], "IDLE")

    def test_one_failing_connect_sequence_does_not_affect_other_car_connect_sequence(self):
        # connect sequence runs only for car_1
        self.ec_a.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        self.ec_a.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec_a.post(command_response("id", CmdResponseType.OK, 0))

        time.sleep(0.5)

        self.ec_a.post(status("id", DeviceState.RUNNING, autonomy, 0, self.payload), sleep=0.1)
        self.ec_b.post(status("id", DeviceState.RUNNING, autonomy, 0, self.payload), sleep=0.1)

        time.sleep(0.5)

        # status for car_1 has been succesfully sent
        statuses = self.api.get_statuses("company_x", "car_a")
        self.assertEqual(len(statuses), 2)
        # no status for car_2 - connect sequence failed
        statuses = self.api.get_statuses("company_x", "car_b")
        self.assertEqual(len(statuses), 0)

    def tearDown(self):
        docker_compose_down()
        comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
