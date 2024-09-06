from __future__ import annotations
import subprocess
import time

from paho.mqtt.client import MQTTMessage as _MQTTMessage
import paho.mqtt.subscribe as subscribe  # type: ignore
import paho.mqtt.publish as publish  # type: ignore
import logging


class MQTTBrokerTest:

    _running_broker_processes: list[subprocess.Popen] = []
    _DEFAULT_HOST = "127.0.0.1"
    _DEFAULT_PORT = 1883

    def __init__(
        self, start: bool = False, port: int = _DEFAULT_PORT, kill_others: bool = True
    ):
        if kill_others:  # pragma: no cover
            MQTTBrokerTest.kill_all_test_brokers()
        self._process: None | subprocess.Popen = None
        self._port = port
        self._host = self._DEFAULT_HOST
        self._script_path = "lib/mqtt-testing/interoperability/startbroker.py"
        if start:
            self.start()

    @classmethod
    def running_processes(cls) -> list[subprocess.Popen]:
        return cls._running_broker_processes

    @classmethod
    def kill_all_test_brokers(cls):  # pragma: no cover
        for process in cls._running_broker_processes:
            print(f"Killing test broker process '{process.pid}'.")
            process.kill()
            try:
                cls._running_broker_processes.remove(process)
            except ValueError:
                pass

    @property
    def is_running(self) -> bool:
        return self._process is not None

    def collect_published(self, topic: str, n: int = 1) -> list[_MQTTMessage]:
        """Return messages from the broker on the given topic.

        `n` is the number of messages to wait for and return.
        """
        print(f"Test broker: Waiting for {n} messages on topic {topic}")
        result = subscribe.simple(
            topics=[topic], hostname=self._host, port=self._port, msg_count=n
        )
        if n == 0:  # pragma: no cover
            return []
        if n == 1:
            return [result]
        else:
            return result

    def publish(self, topic: str, *payload: bytes) -> None:
        if not payload:  # pragma: no cover
            return
        payloads: list[bytes] = []
        for p in payload:
            payloads.append(p)
        if len(payloads) == 1:
            publish.single(
                topic, payload=payload[0], hostname=self._host, port=self._port
            )
        else:
            try:
                publish.multiple(msgs=[(topic, p) for p in payloads], hostname=self._host, port=self._port)  # type: ignore
                print(f"Test broker: Published messages to topic {topic}.")
            except Exception as e:  # pragma: no cover
                raise e

    def start(self, sleep: float = 1):
        if self.is_running:
            print("Test broker is already running.")
        broker_script = self._script_path
        self._process = subprocess.Popen(
            ["python3", broker_script, f"--port={self._port}"]
        )
        print(f"Started test broker on host {self._host} and port {self._port}")
        assert isinstance(self._process, subprocess.Popen)
        self._running_broker_processes.append(self._process)
        time.sleep(sleep)

    def stop(self):
        """Stop the broker process to stop all communication and free up the port."""
        if not self.is_running:
            print("Test broker is already stopped.")
        elif self._process:
            self._process.terminate()
            self._process.wait()
            assert self._process.poll() is not None
            if self._process in self._running_broker_processes:  # pragma: no cover
                self._running_broker_processes.remove(self._process)
            self._process = None
            MQTTBrokerTest.kill_all_test_brokers()
            time.sleep(0.1)
