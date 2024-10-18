import unittest
import time
from concurrent import futures
from google.protobuf.json_format import MessageToDict  # type: ignore

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
    AutonomyState,
    AutonomyStatus,
    Device,
    device_id,
    DeviceState,
    position,
    status,
    station,
    autonomy_status_data,
    telemetry,
)
from ExternalProtocol_pb2 import ExternalServer as ExternalServerMsg  # type: ignore


autonomy = device_obj(module_id=1, device_type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, device_type=1, role="driving", name="Autonomy")
API_HOST = "http://localhost:8080/v2/protocol"


_comm_layer = communication_layer()


class Test_Succesfull_Communication_With_Single_Device(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(autonomy=autonomy, ext_client=self.ec)

    def test_status_sent_after_successful_connect_sequence_from_device_is_available_on_api(
        self,
    ):
        # send status message
        payload = autonomy_status_data(
            state=AutonomyState.DRIVE,
            telemetry=telemetry(4.5, 0.85, position(49.5, 16.14, 123.5)),
            next_stop=station("stop_a", position(49.1, 16.0, 123.4)),
        )
        self.ec.post(
            status(
                session_id="id",
                state=DeviceState.RUNNING,
                device=autonomy,
                counter=1,
                payload=payload.SerializeToString(),
            ),
            sleep=0.1,
        )
        time.sleep(0.5)
        data_on_api = self.api_client.get_statuses("company_x", "car_a")[-1].payload.data.to_dict()
        data_sent = MessageToDict(payload)
        self.assertEqual(data_on_api["state"], data_sent["state"])
        self.assertDictEqual(data_on_api["telemetry"], data_sent["telemetry"])
        self.assertDictEqual(data_on_api["nextStop"], data_sent["nextStop"])

    def test_command_posted_on_api_after_connect_sequence_is_forwarded_to_device(self):
        cmd = api_autonomy_command(
            device_id=device_id(1, 1, "driving", "Autonomy"),
            action=Action.START,
            stops=[station("stop_a", position(49.1, 16.0, 123.4))],
            route="route_1",
        )
        with futures.ThreadPoolExecutor() as ex:
            s = self.api_client.get_statuses("company_x", "car_a")
            self.assertEqual(len(s), 1)
            f = ex.submit(self.ec.get, n=1)
            self.api_client.post_commands("company_x", "car_a", cmd)
            time.sleep(0.5)
            msg = f.result()[0]
            msg = ExternalServerMsg.FromString(msg.payload)
            self.assertEqual(msg.command.deviceCommand.device.deviceName, "Autonomy")
            self.assertEqual(msg.command.deviceCommand.device.deviceRole, "driving")
            self.assertEqual(msg.command.deviceCommand.device.deviceType, 1)
            self.assertEqual(msg.command.deviceCommand.device.module, 1)

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_sequence(self, autonomy: Device, ext_client: ExternalClientMock) -> None:
        ext_client.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        ext_client.post(
            status(
                "id",
                DeviceState.CONNECTING,
                autonomy,
                0,
                payload=AutonomyStatus().SerializeToString(),
            ),
            sleep=0.1,
        )
        ext_client.post(command_response("id", CmdResponseType.OK, 0), sleep=0.5)


class Test_Messages_From_Unsupported_Device(unittest.TestCase):

    def setUp(self) -> None:
        _comm_layer.start()
        self.ec = ExternalClientMock(_comm_layer, "company_x", "car_a")
        self.api_client = ApiClientMock(API_HOST, "TestAPIKey")
        docker_compose_up()
        self._run_connect_sequence(autonomy=autonomy, ext_client=self.ec)

    def test_messages_from_unsupported_device_are_ignored_and_not_forwarded_to_api(
        self,
    ):
        timestamp = int(time.time() * 1000)
        unsupported_device = device_obj(
            module_id=1,
            device_type=123456789,
            role="notdriving",
            name="UnsupportedDevice",
            priority=0,
        )
        self.ec.post(
            status(
                session_id="id",
                state=DeviceState.RUNNING,
                device=autonomy,
                counter=1,
                payload=AutonomyStatus(state=AutonomyStatus.ERROR).SerializeToString(),
            ),
            sleep=0.1,
        )
        self.ec.post(
            status(
                "id",
                DeviceState.CONNECTING,
                unsupported_device,
                2,
                AutonomyStatus().SerializeToString(),
            ),
            sleep=0.1,
        )
        time.sleep(0.1)
        s = self.api_client.get_statuses("company_x", "car_a", since=timestamp)
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0].device_id.module_id, autonomy.module)
        self.assertEqual(s[0].device_id.name, "Autonomy")
        self.assertEqual(s[0].device_id.role, "driving")
        self.assertEqual(s[0].payload.data.to_dict()["state"], "ERROR")
        print(s[0].to_json())

    def tearDown(self):
        docker_compose_down()
        _comm_layer.stop()

    def _run_connect_sequence(self, autonomy: Device, ext_client: ExternalClientMock) -> None:
        ext_client.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.1)
        ext_client.post(
            status(
                "id",
                DeviceState.CONNECTING,
                autonomy,
                0,
                payload=AutonomyStatus().SerializeToString(),
            ),
            sleep=0.1,
        )
        ext_client.post(command_response("id", CmdResponseType.OK, 0), sleep=0.1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
