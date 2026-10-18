"""RAPID programs written by other people, from public repositories.

The files are downloaded when the test runs (at the commits listed here) into
test/public/, a folder ignored by git: they are not part of this project and keep the
license of their repositories. The tests are skipped without network. They check that the
programs that other people wrote pass the validation and, for the server of
open-abb-driver, that it runs on the simulated robot and answers a client on a socket."""

import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from typing import Optional

import pytest

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(PROJECT_DIR, "test", "public")

# name -> (repository, commit, path in the repository)
PROGRAMS = {
    "SERVER.mod": (
        "Humhu/open-abb-driver",
        "c457dc1e658bbcd228387077faf493b620725806",
        "RAPID/SERVER.mod",
    ),
    "LOGGER.mod": (
        "Humhu/open-abb-driver",
        "c457dc1e658bbcd228387077faf493b620725806",
        "RAPID/LOGGER.mod",
    ),
    "mGodel_Main.mod": (
        "Jmeyer1292/abb_file_suite",
        "333a0d76ef229b09e9a6b36b5243ba6fa00bf5df",
        "rapid/mGodel_Main.mod",
    ),
}


def program(name: str) -> str:
    """the path of the downloaded program (skips the test without network)"""
    path = os.path.join(CACHE_DIR, name)
    if not os.path.exists(path):
        repository, commit, source = PROGRAMS[name]
        url = "https://raw.githubusercontent.com/%s/%s/%s" % (repository, commit, source)
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read()
        except OSError as error:  # pragma: no cover
            pytest.skip("cannot download %s: %s" % (url, error))
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
    return path


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_validation_of_public_programs(name: str) -> None:
    result = subprocess.run(
        [sys.executable, "rapidvalidate.py", program(name)],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


class Client:
    """the client of the server of open-abb-driver: messages "code parameters #" and
    answers "code ok data" """

    def __init__(self, port: int, process: "subprocess.Popen[str]") -> None:
        deadline = time.monotonic() + 60
        while True:
            try:
                self.connection = socket.create_connection(("127.0.0.1", port), timeout=60)
                break
            except OSError:
                if process.poll() is not None or time.monotonic() > deadline:
                    raise
                time.sleep(0.2)

    def ask(self, message: str) -> list[str]:
        self.connection.sendall((message + " #").encode())
        return self.connection.recv(1024).decode().split()


def test_open_abb_driver_server(tmp_path: "os.PathLike[str]") -> None:
    pytest.importorskip("pinocchio")
    folder = os.fspath(tmp_path)
    port = free_port()
    with open(program("SERVER.mod")) as f:
        text = f.read()
    # the program of the repository for the local simulation: the address and the port
    text = text.replace("192.168.125.1", "127.0.0.1")
    text = re.sub(r"(PERS num serverPort:=\s*)5000", r"\g<1>%d" % (port,), text)
    server = os.path.join(folder, "SERVER.mod")
    with open(server, "w") as f:
        f.write(text)
    # the robot of the task is given by a comment in a module
    robot = os.path.join(folder, "robot.mod")
    with open(robot, "w") as f:
        f.write("MODULE robot\n    !robot: irb120_3_58\nENDMODULE\n")
    subprocess.run(
        [sys.executable, "rapid2py.py", "-i", server, "-i", robot, "-e", "SERVER.main"]
        + ["-d", folder, "-f", "program.py"],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([os.path.join(PROJECT_DIR, "run"), PROJECT_DIR])
    env.pop("PYRAPID_VIEWER", None)
    process = subprocess.Popen(
        [sys.executable, "program.py"],
        cwd=folder,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        client = Client(port, process)
        assert client.ask("0") == ["0", "1"]  # ping
        assert client.ask("9 1 0 0 0") == ["9", "1"]  # zone: stop points
        assert client.ask("2 0 20 10 0 40 0") == ["2", "1"]  # joint move
        joints = [float(v) for v in client.ask("4")[2:]]
        assert joints == pytest.approx([0, 20, 10, 0, 40, 0], abs=0.01)
        assert client.ask("1 400 100 400 0 0 1 0 0")[:2] == ["1", "1"]  # MoveJ
        pose = [float(v) for v in client.ask("3")[2:5]]
        assert pose == pytest.approx([400, 100, 400], abs=0.5)
        assert client.ask("1 400 -100 300 0 0 1 0 1")[:2] == ["1", "1"]  # MoveL
        pose = [float(v) for v in client.ask("3")[2:5]]
        assert pose == pytest.approx([400, -100, 300], abs=0.5)
        assert client.ask("5 5") == ["5", "0"]  # wrong number of parameters
    finally:
        process.kill()
        process.wait()
