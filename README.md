# external-server-integration-tests

Integration tests of Interface between Module Gateway and External Server, independent of the Server implementation.

# Requirements

- Python (version >= 3.10)
- protoc (version >= 3.21)
- Docker

# Preparation

Create and activate virtual environment and install packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Load the mission module as a submodule

```bash
git submodule update --init --recursive
```

Then copy the mission module .proto file and compile it into Python a module:

```bash
cp lib/mission-module/lib/protobuf-mission-module/MissionModule.proto ./tests/_utils/modules/mission_module/ && \
protoc ./tests/_utils/modules/mission_module/MissionModule.proto --python_out=. --pyi_out=.
```

### Running the tests

In the root folder, run the following
```bash
python -m tests [PATH1] [PATH2] ...
```

Each PATH is specified relative to the `tests` folder. If no PATH is specified, all the tests will run. Otherwise
- when PATH is a directory, the script will run all tests in this directory (and subdirectories),
- when PATH is a Python file, the script will run all tests in the file.

