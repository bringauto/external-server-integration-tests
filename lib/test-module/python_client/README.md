# Internal client examples

This repo contains implementation of Test module device using internal client for fleet protocol v2.
These devices is a virtual button which sends it's current state and expects state of it's LED as response.

#### Preparing environment
Before running example devices, it is good practice to create a virtual environment:
```
python -m venv .venv
source .venv/bin/activate
```
Install dependencies:
```
pip install -r requirements.txt
```

## Button
Button is a simple button device which has one LED attached to it. As status, it sends json with key `"pressed"` indicationg wheter button is pressed. As command, it expects json with key `"lit_up"` indicating the desired state of internal LED.
### Usage
Fake buttons can be run with `run_buttons.py` script. It expects config in `yaml` format which specifies attributes for button or multiple buttons (see `buttons.yaml`):
```yaml
- button1_name:
    type: <int> specifying module specific device type (default is 0)
    role: <str> device role
    priority: <int> device priority (default is 0)

- button2_name:
    ...
```
To run use:
```
python run_buttons.py --ip <server_ip> --port <server_port> --config <path_to_yaml>
```
Multiple fake buttons will be created according to yaml config. They will try to connect to specified server, generate and send their statuses periodically and set their LED states according to commands.

> Manual mode of actual button pressing on keyboard can be specified by `--manual` argument.