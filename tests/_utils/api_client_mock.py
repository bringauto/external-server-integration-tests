import time
import sys
import json

sys.path.append(".")
sys.path.append("lib/fleet-protocol/protobuf/compiled/python")


from fleet_http_client_python import (  # type: ignore
    Configuration,
    ApiClient as _ApiClient,
    ApiException,
    Message,
    DeviceId,
    Payload,
    DeviceApi,
)


class ApiClientMock:

    def __init__(self, host: str, company: str, car: str, api_key: str) -> None:
        self._configuration = Configuration(host=host, api_key={"AdminAuth": api_key})
        self._api_client = _ApiClient(self._configuration)
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
