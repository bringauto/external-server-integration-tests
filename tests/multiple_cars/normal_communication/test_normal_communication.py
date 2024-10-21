import unittest
import time
import concurrent.futures as futures
import json

from tests._utils.api_client_mock import ApiClientMock
from tests._utils.external_client import ExternalClientMock, communication_layer
from tests._utils.docker import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    CmdResponseType,
    api_command,
    command_response,
    connect_msg,
    device_id,
    device_obj,
    status,
)
from ExternalProtocol_pb2 import ExternalServer as ExternalServerMsg  # type: ignore


API_HOST = "http://localhost:8080/v2/protocol"
comm_layer = communication_layer()

button = device_obj(module_id=2, device_type=3, role="test_button", name="Button", priority=0)
button_id = device_id(module_id=2, device_type=3, role="test_button", name="Button")
test_device = device_obj(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")
test_device_id = device_id(module_id=3, device_type=1, role="test_device_1", name="Test_Device_1")


class Test_Normal_Communication(unittest.TestCase):

    def setUp(self) -> None:
        comm_layer.start()
        self.ec_a = ExternalClientMock(comm_layer, "company_x", "car_a")
        self.ec_b = ExternalClientMock(comm_layer, "company_x", "car_b")
        self.api = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up("config_2_cars.json")
        time.sleep(1)

    def test_sending_commands_to_both_car_test_device_devices_and_io_modules(self):
        # connect both cars
        test_device_payload = {"content": "An arbitrary string ...", "timestamp": 111}
        io_payload = {"data": [[], [], {"butPr": 0}]}

        self.ec_a.post(connect_msg("id", "company_x", "car_a", [test_device, button]))
        self.ec_a.post(status("id", "CONNECTING", test_device, 0, test_device_payload))
        self.ec_a.post(status("id", "CONNECTING", button, 1, io_payload), sleep=0.5)
        self.ec_a.post(command_response("id", CmdResponseType.OK, 0))
        self.ec_a.post(command_response("id", CmdResponseType.OK, 1))

        self.ec_b.post(connect_msg("id", "company_x", "car_b", [test_device, button]))
        self.ec_b.post(status("id", "CONNECTING", test_device, 0, test_device_payload))
        self.ec_b.post(status("id", "CONNECTING", button, 1, io_payload))
        self.ec_b.post(command_response("id", CmdResponseType.OK, 0))
        self.ec_b.post(command_response("id", CmdResponseType.OK, 1))

        time.sleep(0.5)

        with futures.ThreadPoolExecutor() as executor:
            f_a = executor.submit(self.ec_a.get, 2)
            f_b = executor.submit(self.ec_b.get, 2)
            time.sleep(1)
            self.api.post_commands(
                "company_x",
                "car_a",
                api_command(test_device_id, {"content": "test_1", "timestamp": 222}),
            )
            time.sleep(0.1)
            self.ec_a.post(command_response("id", CmdResponseType.OK, 2))
            self.api.post_commands(
                "company_x",
                "car_b",
                api_command(test_device_id, {"content": "test_2", "timestamp": 333}),
            )
            time.sleep(0.1)
            self.ec_a.post(command_response("id", CmdResponseType.OK, 2))
            self.api.post_commands(
                "company_x", "car_a", api_command(button_id, [{"outNum": 3, "actType": 2}])
            )
            time.sleep(0.1)
            self.ec_a.post(command_response("id", CmdResponseType.OK, 3))
            self.api.post_commands(
                "company_x", "car_b", api_command(button_id, [{"outNum": 3, "actType": 2}])
            )
            time.sleep(0.1)
            self.ec_a.post(command_response("id", CmdResponseType.OK, 3))

            test_device_cmd_a, io_cmd_a = tuple(f_a.result())
            test_device_cmd_b, io_cmd_b = tuple(f_b.result())

            self.assertEqual(
                ExternalServerMsg.FromString(
                    test_device_cmd_a.payload
                ).command.deviceCommand.device,
                test_device,
            )
            self.assertEqual(
                ExternalServerMsg.FromString(io_cmd_a.payload).command.deviceCommand.device, button
            )
            self.assertEqual(
                ExternalServerMsg.FromString(
                    test_device_cmd_b.payload
                ).command.deviceCommand.device,
                test_device,
            )
            self.assertEqual(
                ExternalServerMsg.FromString(io_cmd_b.payload).command.deviceCommand.device, button
            )
            time.sleep(1)

    def tearDown(self):
        docker_compose_down()
        comm_layer.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
