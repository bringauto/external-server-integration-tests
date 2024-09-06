# External server integration tests

Integration tests of an interface between Module Gateway and External Server, independent of the Server implementation.

All the tests are contained in the `tests` folder. The tests are written in Python and use the `unittest` framework.

The `tests/_utils` folder contains utility functions and classes used in the tests. It does not contain any tests.

# Requirements

- Python (version >= 3.10)
- protoc (version >= 3.21)
- Docker (version >= 27.0)

# Preparation

Create and activate virtual environment, install Python packages:

```bash
python3 -m venv .venv  && \
source .venv/bin/activate && \
pip install -r requirements.txt
```

Load the necessary submodules:

```bash
git submodule update --init --recursive
```

Copy the mission module .proto file and compile it into Python a module:

```bash
cp lib/mission-module/lib/protobuf-mission-module/MissionModule.proto ./tests/_utils/modules/mission_module/ && \
protoc ./tests/_utils/modules/mission_module/MissionModule.proto --python_out=. --pyi_out=.
```

# Running the tests

In the root folder, run the following

```bash
python3 -m tests [PATH1] [PATH2] ...
```

Each PATH is specified relative to the `tests` folder. If no PATH is specified, all the tests will run. Otherwise

- when PATH is a directory, the script will run all tests in this directory (and subdirectories),
- when PATH is a Python file, the script will run all tests in the file.

For example, to run all tests in the `tests/connect_sequence` directory and also single test module from `tests/normal_communication`, run

```bash
python3 -m tests connect_sequence normal_communication/test_communication.py
```

# Development

To add a new test, create a new Python file in the `tests` folder. The file should contain a class that inherits from `unittest.TestCase`. The class should have methods that start with `test_`. Each method should contain the test logic.

To allow for type checking of the classes from compiler protobuf of fleet protocol, add `<project-root-directory>/lib/fleet-protocol/protobuf/compiled/python`to the `PYTHONPATH` environment variable.
