# External server integration tests

Integration tests of an interface between Module Gateway and External Server, independent of the Server implementation.

The server implementation under test in the form of a **Docker image**.

All the tests are contained in the `tests` folder. The tests are written in Python and use the `unittest` framework.

The `tests/_utils` folder contains utility functions and classes used in the tests. It does not contain any tests.

# Requirements

- Python (version >= 3.10)
- Docker (version >= 27.0)

# Setup

## Choosing the implementations to be tested

Copy the `config/tests/empty_config.json` file to `config/tests/config.json`.

For each of the fields in the `config/tests/config.json` file, replace the `<path-to-docker-image>` with the path to the corresponding Docker image.

- `EXTERNAL_SERVER_IMAGE` - the Docker image of the External Server implementation to be tested
- `FLEET_PROTOCOL_HTTP_API_IMAGE` - the Docker image of the Fleet Protocol HTTP API implementation to be used for the tests

## Environment and submodules for testing

In the `requirements.txt` file set the version of `fleet_http_client_python` to the version that is compatible with the version of the Fleet Protocol HTTP API used for testing.

Create and activate a virtual environment and install Python packages:

```bash
python3 -m venv .venv  && \
source .venv/bin/activate && \
pip install -r requirements.txt
```

Load the necessary submodules:

```bash
git submodule update --init --recursive
```

# Running the tests

In the root folder, run the following

```bash
python3 -m tests [PATH1] [PATH2] ...
```

Each PATH is specified relative to the `tests` folder. If no PATH is specified, all the tests will run, Each PATH can be either

1. a directory - the script will run all tests in this directory (and subdirectories),
2. a Python file - the script will run all tests in the file.

For example, to run all tests in the `tests/connect_sequence` directory and also single test module from `tests/normal_communication`, run

```bash
python3 -m tests connect_sequence normal_communication/test_communication.py
```

# Development

## Adding tests

To add a new test, create a new Python file in the `tests` folder. The file should contain a class that inherits from `unittest.TestCase`. The class should have methods that start with `test_`.
Unit test names should describe the purpose of the test, i.e. tell the expected behavior. For example,

```python
def test_names_containing_numerals_raise_exception(self):
    self.assertRaises(NameContainsNumerals, "car_1324")
```

is preferred over

```python
def test_invalid_names(self):
    self.assertRaises(NameContainsNumerals, "car_1324")
```

## Switching the communication protocol

The External server communicates with the car via MQTT. If this is changed, do the following:

- add any necessary utility modules to the `tests/_utils` for the new communication protocol,
- modify the `_CommunicationLayerImpl` class in `tests/_utils/external_client.py` for the new communication protocol.

## MQTT broker

The mocked communication layer between External Client mock and the External Server currently uses the eclipse's test [MQTT broker](https://github.com/eclipse/paho.mqtt.testing), implemented in Python. There is no special reason for using specifically this broker. In case of any issues with the broker, it can be replaced with another (a suitable option is to use the VerneMQ broker, as in [etna](https://github.com/bringauto/etna)).

## Type checking

To allow for type checking of the classes from compiled protobuf files of the Fleet Protocol, add `<project-root-directory>/lib/fleet-protocol/protobuf/compiled/python`to the `PYTHONPATH` environment variable.
