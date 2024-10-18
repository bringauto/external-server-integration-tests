import unittest
import time
import concurrent.futures as futures
import json

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    Action,
    AutonomyStatus,
    CmdResponseType,
    DeviceState,
    api_autonomy_command,
    api_io_command,
    command_response,
    connect_msg,
    device_id,
    device_obj,
    status,
    station,
    position,
)
from ExternalProtocol_pb2 import ExternalServer as ExternalServerMsg  # type: ignore


autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, type=1, role="driving", name="Autonomy")
button = device_obj(module_id=2, type=3, role="io", name="Button", priority=0)
button_id = device_id(module_id=2, type=3, role="io", name="Button")
API_HOST = "http://localhost:8080/v2/protocol"
comm_layer = communication_layer()


class Test_Normal_Communication(unittest.TestCase):

    def setUp(self) -> None:
        comm_layer.start()
        self.ec_a = ExternalClientMock(comm_layer, "company_x", "car_a")
        self.ec_b = ExternalClientMock(comm_layer, "company_x", "car_b")
        self.api = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up("config_2_cars.json")
        time.sleep(1)

    def test_sending_commands_to_both_car_autonomy_devices_and_io_modules(self):
        # connect both cars
        autonomy_payload = AutonomyStatus().SerializeToString()
        payload_dict = {"data": [[], [], {"butPr": 0}]}
        io_payload = json.dumps(payload_dict).encode()

        self.ec_a.post(connect_msg("id", "company_x", "car_a", [autonomy, button]), sleep=0.1)
        self.ec_a.post(
            status("id", DeviceState.CONNECTING, autonomy, 0, autonomy_payload), sleep=0.1
        )
        self.ec_a.post(status("id", DeviceState.CONNECTING, button, 1, io_payload), sleep=0.1)
        self.ec_a.post(command_response("id", CmdResponseType.OK, 0), sleep=0.2)
        self.ec_a.post(command_response("id", CmdResponseType.OK, 1))

        self.ec_b.post(connect_msg("id", "company_x", "car_b", [autonomy, button]), sleep=0.1)
        self.ec_b.post(
            status("id", DeviceState.CONNECTING, autonomy, 0, autonomy_payload), sleep=0.1
        )
        self.ec_b.post(status("id", DeviceState.CONNECTING, button, 1, io_payload), sleep=0.1)
        self.ec_b.post(command_response("id", CmdResponseType.OK, 0), sleep=0.1)
        self.ec_b.post(command_response("id", CmdResponseType.OK, 1))

        time.sleep(0.5)

        with futures.ThreadPoolExecutor() as executor:
            # send command to car_a
            f_a = executor.submit(self.ec_a.get, 2)
            f_b = executor.submit(self.ec_b.get, 2)
            time.sleep(0.5)
            self.api.post_commands(
                "company_x",
                "car_a",
                api_autonomy_command(
                    autonomy_id, Action.START, [station("station_a", position(0, 0, 0))], "route_1"
                ),
            )

            self.api.post_commands(
                "company_x",
                "car_b",
                api_autonomy_command(autonomy_id, Action.NO_ACTION, [], "route_1"),
            )
            self.api.post_commands(
                "company_x", "car_a", api_io_command(button_id, [{"outNum": 3, "actType": 2}])
            )
            self.api.post_commands(
                "company_x", "car_b", api_io_command(button_id, [{"outNum": 3, "actType": 2}])
            )
            time.sleep(1)

            autonomy_cmd_a, io_cmd_a = tuple(f_a.result())
            autonomy_cmd_b, io_cmd_b = tuple(f_b.result())

            self.assertEqual(
                ExternalServerMsg.FromString(autonomy_cmd_a.payload).command.deviceCommand.device,
                autonomy,
            )
            self.assertEqual(
                ExternalServerMsg.FromString(io_cmd_a.payload).command.deviceCommand.device, button
            )
            self.assertEqual(
                ExternalServerMsg.FromString(autonomy_cmd_b.payload).command.deviceCommand.device,
                autonomy,
            )
            self.assertEqual(
                ExternalServerMsg.FromString(io_cmd_b.payload).command.deviceCommand.device, button
            )

    def tearDown(self):
        docker_compose_down()
        comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
