import time
import sys
import abc

sys.path.append("./lib/fleet-protocol/protobuf/compiled/python/ExternalProtocol_pb2.pyi")

from ExternalProtocol_pb2 import ExternalClient as _ExternalClientMsg  # type: ignore
from .broker import MQTTBrokerTest
from paho.mqtt.client import MQTTMessage as _MQTTMessage


class CommunicationLayer(abc.ABC):
    @abc.abstractmethod
    def post(self, company: str, car_name: str, data: bytes) -> None:
        pass

    @abc.abstractmethod
    def collect(self, company: str, car_name: str, n: int) -> list[_MQTTMessage]:
        pass

    @abc.abstractmethod
    def start(self) -> None:
        pass

    @abc.abstractmethod
    def stop(self) -> None:
        pass


class _CommunicationLayerImpl(CommunicationLayer):

    def __init__(self) -> None:
        self._broker = MQTTBrokerTest()

    def post(self, company: str, car_name: str, data: bytes) -> None:
        topic = f"{company}/{car_name}/module_gateway"
        self._broker.publish(topic, data)
        print(f"Published message to {topic}")

    def collect(self, company: str, car_name: str, n: int) -> list[_MQTTMessage]:
        topic = f"{company}/{car_name}/external_server"
        return self._broker.collect_published(topic, n)

    def start(self) -> None:
        self._broker.start()

    def stop(self) -> None:
        self._broker.stop()


def communication_layer() -> CommunicationLayer:
    return _CommunicationLayerImpl()


class ExternalClientMock:

    def __init__(self, communication_layer: CommunicationLayer, company: str, car: str) -> None:
        self._comm_layer = communication_layer
        self._company = company
        self._car = car

    def post(self, msg: _ExternalClientMsg, sleep: float = 0.0) -> None:
        data = msg.SerializeToString()
        self._comm_layer.post(self._company, self._car, data)
        time.sleep(max(sleep, 0.0))

    def get(self, n: int) -> list[_MQTTMessage]:
        return self._comm_layer.collect(self._company, self._car, n)
