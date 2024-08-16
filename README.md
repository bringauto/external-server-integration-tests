# external-server-integration-tests

Integration tests of Interface between Module Gateway and External Server, independent of the Server implementation.

# Requirements

- Python (version >= 3.10)
- [protobuf](https://github.com/protocolbuffers/protobuf) (version >= 3.21.0)


# Preparation
Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Python packages must be installed by running the following command from the root directory.

```bash
pip install -r requirements.txt -r lib/example-module/python_client/requirements.txt
```

Load the mission module as a submodule

```bash
git submodule update mission-module --init --recursive
```

Then copy the mission module .proto file and compile it into Python a module:

```bash
cp lib/mission-module/lib/protobuf-mission-module/MissionModule.proto ./tests/autonomy_messages/ && \
protoc ./tests/autonomy_messages/MissionModule.proto --python_out=. --pyi_out=.
```
