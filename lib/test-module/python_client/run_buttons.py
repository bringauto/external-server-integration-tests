import json
import logging
from dataclasses import dataclass
import asyncio
import os
import argparse

import yaml
from rich.logging import RichHandler

from internal_client import InternalClient, exceptions
from button_logic import ButtonLogic, ButtonState, ButtonLedState

MODULE_ID = 1000


@dataclass
class ButtonClientConfig:
    device_name: str
    device_type: int
    device_role: str
    device_priority: int = 0

    def __repr__(self) -> str:
        return f"(name={self.device_name}, type={self.device_type}, role={self.device_role}, priority={self.device_priority})"

    @staticmethod
    def load_config(file_name: str) -> list["ButtonClientConfig"]:
        if not os.path.isfile(file_name):
            raise FileNotFoundError(f"Config file not found: {file_name}")
        with open(file_name, "r") as f_in:
            try:
                cfg = yaml.safe_load(f_in)
            except yaml.parser.ParserError:
                raise ValueError(f"Config file can not be parsed as YAML") from None

        button_configs = []
        for button in cfg:
            button_name = list(button.keys())[0]
            try:
                button_role = button[button_name]["role"]
                button_type = int(button[button_name].get("type", 0))
                button_priority = int(button[button_name].get("priority", 0))
            except KeyError:
                raise ValueError(f"Missing required field in {button_name} config.") from None
            except ValueError:
                raise ValueError(f"Invalid value in {button_name} config.") from None

            button_configs.append(
                ButtonClientConfig(button_name, button_type, button_role, button_priority)
            )

        return button_configs


class ButtonClient:

    def __init__(self, server_ip: str, server_port: int, button_config: ButtonClientConfig, manual_mode: bool) -> None:
        self.server_connection = (server_ip, server_port)
        self.device_name = button_config.device_name
        self.device_type = button_config.device_type
        self.device_role = button_config.device_role
        self.manual_mode = manual_mode

        self.device_priority = button_config.device_priority

        self.logger = logging.getLogger(f"{self.device_name}")
        self.button = ButtonLogic(logger=self.logger, manual_mode=manual_mode)

    async def start(self) -> None:
        if not self._connect():
            return

        while True:
            state_data = self._get_state_data()
            try:
                self.client.send_status(state_data, timeout=5)
            except (exceptions.CommunicationExceptions, exceptions.ConnectExceptions) as e:
                self.logger.error(f"Send status unsuccessful: {e}")
                break

            command_data = self.client.get_command()
            try:
                self._handle_command_data(command_data)
            except ValueError as e:
                self.logger.error(f"Invalid Command: {e}")
                break
            if not self.manual_mode:
                await asyncio.sleep(5)

        self.client.destroy()

    def _connect(self) -> bool:
        try:
            self.client = InternalClient(
                MODULE_ID,
                self.server_connection[0],
                self.server_connection[1],
                self.device_name,
                self.device_type,
                self.device_role,
                self.device_priority,
            )
        except exceptions.ConnectExceptions as e:
            self.logger.error(
                f"Button could not connect because server responsed with: {type(e)}"
            )
            return False
        except exceptions.CommunicationExceptions as e:
            self.logger.error(f"Connection to server could not be established due to: {e}")
            return False

        return True

    def _get_state_data(self) -> bytes:
        button_state = self.button.get_button_state()
        binary_data = json.dumps({"pressed": button_state == ButtonState.PRESSED}).encode()
        return binary_data

    def _handle_command_data(self, command_data: bytes) -> None:
        try:
            data_json = json.loads(command_data)
        except json.JSONDecodeError:
            raise ValueError(f"Couldn't parse json from binary commandData")

        try:
            led_command = data_json["lit_up"]
            assert type(led_command) == bool
        except (KeyError, AssertionError):
            raise ValueError(f"commandData json has invalid structure")

        self.button.set_led_state(ButtonLedState(led_command))


async def run_buttons(
    server_ip: str, server_port: int, button_configs: list[ButtonClientConfig], manual_mode: bool
) -> None:
    logger = logging.getLogger("TaskRunner")
    buttons = [ButtonClient(server_ip, server_port, cfg, manual_mode) for cfg in button_configs]
    tasks = []
    for button, button_cfg in zip(buttons, button_configs):
        logger.info(f"Starting button {button_cfg}")
        tasks.append(asyncio.create_task(button.start()))

    for task in tasks:
        await task

    logger.info("All buttons finished")


if __name__ == "__main__":
    FORMAT = "%(name)s:%(message)s"
    logging.basicConfig(
        level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--ip", type=str, default="127.0.0.1", help="IP address of server"
    )
    parser.add_argument("-m", "--manual", type=bool, default=False, help="Set manual mode, buttons will expect input from keyboard in order to be pressed")
    parser.add_argument("-p", "--port", type=int, default=8888, help="Port of server")
    parser.add_argument(
        "-cfg",
        "--config",
        type=str,
        default="buttons.yaml",
        help="Path to yaml button config file",
    )
    args = parser.parse_args()

    try:
        buttons = ButtonClientConfig.load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        logging.error(e)
        exit(1)

    try:
        asyncio.run(run_buttons(args.ip, args.port, buttons, args.manual))
    except KeyboardInterrupt:
        logging.info("Shuting down.")
