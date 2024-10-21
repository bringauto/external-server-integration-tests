import sys

sys.path.append("lib/fleet-protocol/protobuf/compiled/python")


from fleet_http_client_python import (  # type: ignore
    Configuration,
    ApiClient as _ApiClient,
    ApiException,
    Message,
    DeviceApi,
)


class ApiClientMock:

    def __init__(self, host: str, api_key: str) -> None:
        self._configuration = Configuration(host=host, api_key={"AdminAuth": api_key})
        self._api_client = _ApiClient(self._configuration)
        self._message_api = DeviceApi(api_client=self._api_client)

    def post_commands(self, company: str, car: str, *commands: Message) -> None:
        """Post list of commands to the API."""
        resp = self._message_api.send_commands_with_http_info(
            company_name=company, car_name=car, message=list(commands)
        )
        print("API Client Mock response on post command request: ", resp)

    def post_statuses(self, company: str, car: str, *statuses: Message) -> None:
        """Post list of commands to the API."""
        self._message_api.send_statuses(company_name=company, car_name=car, message=list(statuses))

    def get_statuses(
        self, company: str, car: str, since: int = 0, wait: bool = False
    ) -> list[Message]:
        """Return list of stastuses from the API inclusively newer than `since` timestamp (in milliseconds)."""
        try:
            return self._message_api.list_statuses(
                company_name=company, car_name=car, since=since, wait=wait
            )
        except ApiException as e:
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []
