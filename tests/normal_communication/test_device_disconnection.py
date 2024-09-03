import unittest
import time
import json

from tests._utils.broker import MQTTBrokerTest
from tests._utils.misc import clear_logs
from tests._utils.mocks import (
    ApiClientTest,
    ExternalClientMock,
    docker_compose_down,
    docker_compose_up,
)
from tests._utils.messages import (
    connect_msg,
    command_response,
    device_obj,
    DeviceState,
    DeviceId,
    status,
    CmdResponseType,
)


API_HOST = "http://localhost:8080/v2/protocol"
_broker = MQTTBrokerTest()
button_1 = device_obj(module_id=2, type=3, role="button_1", name="Button1", priority=0)
button_1_id = DeviceId(module_id=2, type=3, role="button_1", name="Button1")
button_2 = device_obj(module_id=2, type=3, role="button_2", name="Button2", priority=0)


class Test_Device_Disconnection(unittest.TestCase):

    def setUp(self) -> None:
        self.broker = _broker
        self.broker.start()
        clear_logs()
        self.ec = ExternalClientMock(self.broker, "company_x", "car_a")
        self.api_client = ApiClientTest(API_HOST, "company_x", "car_a", "TestAPIKey")
        docker_compose_up()

    def test_statuses_of_disconnected_device_are_not_forwarded_to_api(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [button_1, button_2]))
        payload_dict = {"data": [[], [], {"butPr": 0}]}
        payload = json.dumps(payload_dict).encode()
        self.ec.post(status("id", DeviceState.CONNECTING, button_1, 0, payload))
        self.ec.post(status("id", DeviceState.CONNECTING, button_2, 1, payload))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))
        time.sleep(0.1)

        self.ec.post(status("id", DeviceState.DISCONNECT, button_1, 2, payload))

        time.sleep(0.1)
        timestamp = int(1000*time.time())

        self.ec.post(status("id", DeviceState.RUNNING, button_2, 3, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_1, 4, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_2, 5, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_1, 6, payload))

        time.sleep(0.1)
        statuses = self.api_client.get_statuses(since=timestamp)
        # the status from button_1 is not present in the list of statuses
        self.assertEqual(len(statuses), 2)
        self.assertNotIn(button_1_id, [status.device_id for status in statuses])

    def test_statuses_of_connected_device_are_again_forwarded_to_api(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [button_1, button_2]))
        payload_dict = {"data": [[], [], {"butPr": 0}]}
        payload = json.dumps(payload_dict).encode()
        self.ec.post(status("id", DeviceState.CONNECTING, button_1, 0, payload))
        self.ec.post(status("id", DeviceState.CONNECTING, button_2, 1, payload))
        self.ec.post(command_response("id", CmdResponseType.OK, 0))
        self.ec.post(command_response("id", CmdResponseType.OK, 1))
        time.sleep(0.1)

        self.ec.post(status("id", DeviceState.DISCONNECT, button_1, 2, payload))

        time.sleep(0.1)

        self.ec.post(status("id", DeviceState.CONNECTING, button_1, 3, payload))

        time.sleep(0.1)

        timestamp = int(1000*time.time())

        self.ec.post(status("id", DeviceState.RUNNING, button_2, 4, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_1, 5, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_2, 6, payload))
        self.ec.post(status("id", DeviceState.RUNNING, button_1, 7, payload))

        time.sleep(0.1)
        statuses = self.api_client.get_statuses(since=timestamp)
        # the status from button_1 is not present in the list of statuses
        self.assertEqual(len(statuses), 4)
        self.assertIn(button_1_id, [status.device_id for status in statuses])

    def tearDown(self) -> None:
        self.broker.stop()
        docker_compose_down()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
