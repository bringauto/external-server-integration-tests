from enum import Enum
import random
from typing import Literal
from logging import Logger

from inputimeout import inputimeout, TimeoutOccurred


class ButtonState(Enum):
    NOT_PRESSED = 0
    PRESSED = 1


class ButtonLedState(Enum):
    OFF = 0
    ON = 1


class ButtonLogic:
    NOT_PRESSED_CHANGE_PROB = 0.4
    PRESSED_CHANGE_PROB = 0.6

    def __init__(self, logger: Logger, manual_mode: bool) -> None:
        self.button_state = ButtonState.NOT_PRESSED
        self.led_state = ButtonLedState.OFF
        self.logger = logger
        self.manual_mode = manual_mode

    def get_button_state(self) -> Literal[ButtonState.NOT_PRESSED, ButtonState.PRESSED]:
        if self.manual_mode:
            try:
                c = inputimeout(prompt='', timeout=1)
            except TimeoutOccurred:
                c = ''
            if self.button_state == ButtonState.NOT_PRESSED:
                if len(c) > 0:
                    self.button_state = ButtonState.PRESSED
            elif self.button_state == ButtonState.PRESSED:
                if len(c) == 0:
                    self.button_state = ButtonState.NOT_PRESSED
        else:
            if self.button_state == ButtonState.NOT_PRESSED:
                if random.random() < self.NOT_PRESSED_CHANGE_PROB:
                    self.button_state = ButtonState.PRESSED
            elif self.button_state == ButtonState.PRESSED:
                if random.random() < self.PRESSED_CHANGE_PROB:
                    self.button_state = ButtonState.NOT_PRESSED

        state_str = (
            "[bold]NOT_PRESSED[/]"
            if self.button_state == ButtonState.NOT_PRESSED
            else "[bold green]PRESSED[/]"
        )
        self.logger.info(f"Button state {state_str}", extra={"markup": True})
        return self.button_state

    def set_led_state(self, state) -> None:
        self.led_state = state
        state_str = (
            "[bold]OFF[/]"
            if self.led_state == ButtonLedState.OFF
            else "[bold green]ON[/]"
        )
        self.logger.info(f"LED state {state_str}", extra={"markup": True})
