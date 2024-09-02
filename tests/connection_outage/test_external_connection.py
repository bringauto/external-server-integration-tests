import unittest
import json
import time

from tests._utils.misc import clear_logs
from tests._utils.broker import MQTTBrokerTest
from tests._utils.mocks import ApiClientTest, ExternalClientMock
from tests._utils.mocks import docker_compose_up, docker_compose_down
from tests._utils.messages import (
    AutonomyStatus,
    command_response,
    connect_msg,
    device_obj,
    CmdResponseType,
    DeviceState,
    status,
)


API_HOST = "http://localhost:8080/v2/protocol"
_broker = MQTTBrokerTest()
autonomy = device_obj(module_id=1, type=1, role="driving", name="Autonomy", priority=0)


class Test_No_Status_From_Module_Gateway_For_Long_Time(unittest.TestCase):

    def setUp(self) -> None:
        self.broker = _broker
        self.ec = ExternalClientMock(self.broker, "company_x", "car_a")
        self.api_client = ApiClientTest(API_HOST, "company_x", "car_a", "TestAPIKey")
        clear_logs()
        docker_compose_up()
        self.payload = AutonomyStatus().SerializeToString()

    def test_new_connection_sequence_is_accepted_after_mqtt_timeout(self):
        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.2)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0))

        # mqtt connection times out when no message is published by the external client for a long time
        mqtt_timeout = json.load(open("config/external-server/config.json"))["mqtt_timeout"]
        time.sleep(mqtt_timeout + 2)

        self.ec.post(connect_msg("id", "company_x", "car_a", [autonomy]), sleep=0.2)
        self.ec.post(status("id", DeviceState.CONNECTING, autonomy, 0, self.payload), sleep=0.1)
        self.ec.post(command_response("id", CmdResponseType.OK, 0))

        s = self.api_client.get_statuses()
        self.assertEqual(len(s), 2)

    def tearDown(self) -> None:
        docker_compose_down()


if __name__ == "__main__":  # pragma: no cover
    _broker.start()
    unittest.main()
    _broker.stop()
