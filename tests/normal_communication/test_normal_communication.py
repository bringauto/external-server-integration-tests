import unittest
import sys
import subprocess
import os
import time
from concurrent import futures
from google.protobuf.json_format import MessageToDict  # type: ignore

sys.path.append(".")

from tests.utils.broker import MQTTBrokerTest
from tests.utils.mocks import ApiClientTest, ExternalClientMock, run_from_docker_compose
from tests.utils.messages import (
    Action,
    api_command,
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
    status_data,
    telemetry,
)
from ExternalProtocol_pb2 import ExternalServer as ExternalServerMsg  # type: ignore


def clear_logs() -> None:
    if os.path.isfile("./log/external-server/external_server.log"):
        os.remove("./log/external-server/external_server.log")
    if os.path.isfile("./log/module-gateway/ModuleGateway.log"):
        os.remove("./log/module-gateway/ModuleGateway.log")


autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)
autonomy_id = device_id(module_id=1, type=1, role="driving", name="Autonomy")
API_HOST = "http://localhost:8080/v2/protocol"


class Test_Succesfull_Communication_With_Single_Device(unittest.TestCase):

    def setUp(self) -> None:
        clear_logs()
        self.broker = MQTTBrokerTest(start=True)
        self.ec = ExternalClientMock(self.broker, "company_x", "car_a")
        self.api_client = ApiClientTest(API_HOST, "company_x", "car_a", "TestAPIKey")
        run_from_docker_compose()
        self._run_connect_sequence(autonomy=autonomy, ext_client=self.ec)
        time.sleep(1)

    def test_status_sent_after_successful_connect_sequence_from_device_is_available_on_api(self):
        # send status message
        payload = status_data(
            state=AutonomyState.DRIVE,
            telemetry=telemetry(4.5, 0.85, position(49.5, 16.14, 123.5)),
            next_stop=station("stop_a", position(49.1, 16.0, 123.4)),
        )
        self.ec.post(
            status("id", DeviceState.RUNNING, autonomy, 1, payload.SerializeToString()), sleep=0.1
        )
        time.sleep(0.5)
        data_on_api = self.api_client.get_statuses()[-1].payload.data.to_dict()
        data_sent = MessageToDict(payload)
        self.assertEqual(data_on_api["state"], data_sent["state"])
        self.assertDictEqual(data_on_api["telemetry"], data_sent["telemetry"])
        self.assertDictEqual(data_on_api["nextStop"], data_sent["nextStop"])

    def test_command_posted_on_api_after_connect_sequence_is_forwarded_to_device(self):
        cmd = api_command(
            device_id=device_id(1, 1, "driving", "Autonomy"),
            action=Action.START,
            stops=[station("stop_a", position(49.1, 16.0, 123.4))],
            route="route_1",
        )
        with futures.ThreadPoolExecutor() as ex:
            s = self.api_client.get_statuses()
            self.assertEqual(len(s), 1)
            f = ex.submit(
                self.broker.collect_published, topic="company_x/car_a/external_server", n=1
            )
            self.api_client.post_commands(cmd)
            time.sleep(1)
            msg = f.result()[0]
            msg = ExternalServerMsg.FromString(msg.payload)
            self.assertEqual(msg.command.deviceCommand.device.deviceName, "Autonomy")
            self.assertEqual(msg.command.deviceCommand.device.deviceRole, "driving")
            self.assertEqual(msg.command.deviceCommand.device.deviceType, 1)
            self.assertEqual(msg.command.deviceCommand.device.module, 1)

    def tearDown(self):
        subprocess.run(["docker", "compose", "down"])
        self.broker.stop()

    def _run_connect_sequence(self, autonomy: Device, ext_client: ExternalClientMock) -> None:
        ext_client.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.2)
        ext_client.post(
            status(
                "id",
                DeviceState.CONNECTING,
                autonomy,
                0,
                payload=AutonomyStatus().SerializeToString(),
            ),
            sleep=0.2,
        )
        ext_client.post(command_response("id", CmdResponseType.OK, 0))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
