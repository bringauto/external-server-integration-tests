import subprocess
import time
import json


env = json.load(open("./config/tests/config.json"))


def docker_compose_up(config_name: str = "config.json") -> None:
    env["CONFIG_NAME"] = config_name
    subprocess.run(["docker", "compose", "down", "-t", "0"], env=env)
    subprocess.run(["docker", "compose", "up", "--build", "-d"], env=env)
    time.sleep(1)


def docker_compose_down() -> None:
    subprocess.run(["docker", "compose", "down", "-t", "0"], env=env)
