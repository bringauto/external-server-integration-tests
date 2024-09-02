import time
import subprocess
import sys
import json

sys.path.append(".")
sys.path.append("lib/fleet-protocol/protobuf/compiled/python")


from fleet_http_client_python import (  # type: ignore
    Configuration,
    ApiClient,
    ApiException,
    Message,
    DeviceId,
    Payload,
    DeviceApi,
)
from ExternalProtocol_pb2 import ExternalClient as _ExternalClientMsg  # type: ignore
from .broker import MQTTBrokerTest


def run_from_docker_compose() -> None:
    subprocess.run(["docker", "compose", "up", "--build", "-d"])
    time.sleep(1)


class ApiClientTest:

    def __init__(self, host: str, company: str, car: str, api_key: str) -> None:
        self._configuration = Configuration(host=host, api_key={"AdminAuth": api_key})
        self._api_client = ApiClient(self._configuration)
        self._message_api = DeviceApi(api_client=self._api_client)
        self._car = car
        self._company = company

    def command(self, command_data: bytes) -> Message:
        """Create a command message."""
        payload_dict = {
            "encoding": "JSON",
            "message_type": "COMMAND",
            "data": json.dumps(command_data.decode()),
        }
        payload = Payload.from_dict(payload_dict)
        cmd = Message(
            device_id=DeviceId(module_id=1, type=1, role="driving", name="Autonomy"),
            timestamp=int(time.time() * 1000),
            payload=payload,
        )
        return cmd

    def post_commands(self, *commands: Message) -> None:
        """Post list of commands to the API."""
        resp = self._message_api.send_commands_with_http_info(
            company_name=self._company, car_name=self._car, message=list(commands)
        )
        print("API Client Mock response on post command request: ", resp)

    def post_statuses(self, *statuses: Message) -> None:
        """Post list of commands to the API."""
        self._message_api.send_statuses(
            company_name=self._company, car_name=self._car, message=list(statuses)
        )

    def get_statuses(self, since: int = 0, wait: bool = False) -> list[Message]:
        """Return list of stastuses from the API inclusively newer than `since` timestamp (in milliseconds)."""
        try:
            return self._message_api.list_statuses(
                company_name=self._company, car_name=self._car, since=since, wait=wait
            )
        except ApiException as e:
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []


class ExternalClientMock:

    def __init__(self, broker: MQTTBrokerTest, company: str, car: str) -> None:
        self._broker = broker
        self._company = company
        self._car = car

    def post(self, msg: _ExternalClientMsg, sleep: float = 0.0) -> None:
        topic = f"{self._company}/{self._car}/module_gateway"
        msg_str = msg.SerializeToString()
        self._broker.publish(topic, msg_str)
        time.sleep(max(sleep, 0.0))
