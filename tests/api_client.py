from fleet_http_client_python import (   # type: ignore
    Configuration,
    ApiClient,
    Message,
    DeviceId,
    Payload,
    DeviceApi
)
import time
import sys
import json

sys.path.append(".")
sys.path.append("lib/fleet-protocol/protobuf/compiled/python")


class HttpApiClientTest:

    def __init__(self, host: str, company: str, car: str, api_key: str) -> None:
        self._configuration = Configuration(host=host, api_key={'AdminAuth': api_key})
        self._api_client = ApiClient(self._configuration)
        self._message_api = DeviceApi(api_client=self._api_client)

        self._car = car
        self._company = company

    def command(self, command_data: bytes) -> Message:
        """Create a command message."""
        payload_dict = {
            "encoding": "JSON",
            "message_type": "COMMAND",
            "data": json.dumps(command_data.decode())
        }
        payload = Payload.from_dict(payload_dict)
        cmd = Message(
            device_id=DeviceId(module_id=1, type=1, role="driving", name="Autonomy"),
            timestamp=int(time.time()*1000),
            payload=payload
        )
        return cmd

    def post_commands(self, command_data: list[dict]) -> None:
        """Post list of commands to the API."""
        commands = []
        for data in command_data:
            payload_dict = {
                "encoding": "JSON",
                "message_type": "COMMAND",
                "data": data
            }
            payload = Payload.from_dict(payload_dict)
            cmd = Message(
                device_id=DeviceId(module_id=1, type=1, role="driving", name="Autonomy"),
                timestamp=int(time.time()*1000),
                payload=payload
            )
            commands.append(cmd)
            print("Created command: ", cmd.to_dict())
        self._message_api.send_commands(company_name=self._company, car_name=self._car, message=commands)

    def get_statuses(self, since: int = 0, wait: bool = False) -> list[Message]:
        """Return list of statuses from the API inclusively newer than `since` timestamp (in milliseconds)."""
        return self._message_api.list_statuses(company_name=self._company, car_name=self._car, since=since, wait=wait)