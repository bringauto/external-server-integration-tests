import unittest
import sys
import subprocess
import time

sys.path.append(".")

from tests.broker import MQTTBrokerTest


class Test_Succesfull_Communication_With_Single_Device(unittest.TestCase):

    def setUp(self) -> None:
        self.broker = MQTTBrokerTest(start=True)
        time.sleep(1)
        subprocess.run(["docker", "compose", "up", "-d"])
        self.module_process = subprocess.Popen(
            [
                "python3",
                "lib/example-module/python_client/run_buttons.py",
                "--ip",
                "127.0.0.1",
                "--port",
                "1636",
                "--config",
                "lib/example-module/python_client/buttons.yaml"
            ]
        )

    def test_succesfull_communication_with_single_device(self):
        time.sleep(10)

    def tearDown(self):
        self.module_process.terminate()
        subprocess.run(["docker", "compose", "down"])
        self.broker.stop()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
