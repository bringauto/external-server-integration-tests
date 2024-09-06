import subprocess
import time


def docker_compose_up() -> None:
    subprocess.run(["docker", "compose", "down", "-t", "0"])
    subprocess.run(["docker", "compose", "up", "--build", "-d"])
    time.sleep(1)


def docker_compose_down() -> None:
    subprocess.run(["docker", "compose", "down", "-t", "0"])
