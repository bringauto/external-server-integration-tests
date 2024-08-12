import unittest
import sys

sys.path.append('.')

from tests.broker import MQTTBrokerTest


class Test_(unittest.TestCase):

    def test_(self):
        broker = MQTTBrokerTest(start=True)



if __name__ == '__main__':  # pragma: no cover
    unittest.main()