"""rapid2py test: .mod -> rapid2py -> .py, the generated module must be valid Python.

Each conversion runs rapid2py.py in its own process, as from the command line
(standard symbols of default/*.sys included), because the symbol table of
run.pyrapid is a process-wide singleton.

rapid2py validates the program with rapidvalidate before the translation: the
valid test files must be translated, the files that are not valid RAPID must be
rejected with the diagnostics of rapidvalidate.
"""

import functools
import glob
import os
import pathlib
import re
import subprocess
import sys
from typing import Any

import pytest

import rapidvalidate

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(PROJECT_DIR, "test")
# *.ast.mod / *.source.mod / rapid_program.mod are outputs of other tests
MOD_FILES = sorted(
    f
    for f in glob.glob(os.path.join(TEST_DIR, "*.mod"))
    if not f.endswith((".ast.mod", ".source.mod", "rapid_program.mod"))
)


@functools.lru_cache(maxsize=None)
def is_valid(path: str) -> bool:
    return not any(d.severity == rapidvalidate.ERROR for d in rapidvalidate.validate_files([path]))


def rapid2py(path: str, outdir: str, *options: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        [sys.executable, "rapid2py.py", *options, "-i", path, "-d", outdir]
        + ["-f", "rapid_program.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("path", [f for f in MOD_FILES if is_valid(f)], ids=os.path.basename)
def test_rapid2py_generates_valid_python(path: str, tmp_path: pathlib.Path) -> None:
    outdir = os.fspath(tmp_path)
    result = rapid2py(path, outdir)
    # stdout is the (long) AST dump made on error, stderr ends with the traceback
    assert result.returncode == 0, result.stderr[-2000:]

    pyfile = os.path.join(outdir, "rapid_program.py")
    with open(pyfile, "r") as f:
        source = f.read()
    compile(source, pyfile, "exec")


@pytest.mark.parametrize("path", [f for f in MOD_FILES if not is_valid(f)], ids=os.path.basename)
def test_rapid2py_rejects_invalid_rapid(path: str, tmp_path: pathlib.Path) -> None:
    result = rapid2py(path, os.fspath(tmp_path))
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    expected = [
        (d.line, d.code)
        for d in rapidvalidate.validate_files([path])
        if d.severity == rapidvalidate.ERROR
    ]
    found = [
        (int(m.group(1)), m.group(2))
        for m in re.finditer(r"^.*?:(\d+): error: .* \[([a-z-]+)\]$", result.stderr, re.M)
    ]
    assert found == expected, result.stderr


EXEC_DIR = os.path.join(TEST_DIR, "exec")
EXEC_FILES = sorted(glob.glob(os.path.join(EXEC_DIR, "*.mod")))


@pytest.mark.parametrize("path", EXEC_FILES, ids=os.path.basename)
def test_rapid2py_execution(path: str, tmp_path: pathlib.Path) -> None:
    """translate test/exec/<name>.mod, run its main and compare stdout with <name>.out
    (the programs with a robot, !robot:, use the motion instructions of standard.sys)"""
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path, "r") as f:
        robot = "!robot:" in f.read()
    if robot:
        # the motion instructions are in default/standard.sys
        pytest.importorskip("pinocchio")
    outdir = os.fspath(tmp_path)
    result = subprocess.run(
        [sys.executable, "rapid2py.py"]
        + ([] if robot else ["-s"])
        + ["-e", name + ".main", "-i", path, "-d", outdir, "-f", "program.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr[-2000:]

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([os.path.join(PROJECT_DIR, "run"), PROJECT_DIR])
    # one line for each motion instruction, no viewer
    env["PYRAPID_MOTION_LOG"] = "1"
    env.pop("PYRAPID_VIEWER", None)
    run = subprocess.run(
        [sys.executable, "program.py"],
        cwd=outdir,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert run.returncode == 0, run.stderr[-2000:]
    with open(os.path.join(EXEC_DIR, name + ".out"), "r") as f:
        assert run.stdout == f.read()


def test_rapid2py_run(tmp_path: pathlib.Path) -> None:
    """-r runs the translated program; -d creates the output folder"""
    path = os.path.join(EXEC_DIR, "operators.mod")
    outdir = os.path.join(os.fspath(tmp_path), "a", "b")
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "rapid2py.py", "-s", "-r", "-e", "operators.main"]
        + ["-i", path, "-d", outdir, "-f", "program.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    with open(os.path.join(EXEC_DIR, "operators.out"), "r") as f:
        assert result.stdout.endswith(f.read())


def test_rapid2rapid_creates_folder(tmp_path: pathlib.Path) -> None:
    outdir = os.path.join(os.fspath(tmp_path), "a", "b")
    result = subprocess.run(
        [sys.executable, "rapid2rapid.py", "-i", os.path.join(TEST_DIR, "test2.mod")]
        + ["-d", outdir, "-f", "test2.mod"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert os.path.exists(os.path.join(outdir, "test2.mod"))


def test_example_irb120(tmp_path: pathlib.Path) -> None:
    """examples/irb120/demo.mod runs to the end"""
    pytest.importorskip("pinocchio")
    env = dict(os.environ)
    env["PYRAPID_MOTION_LOG"] = "1"
    env.pop("PYRAPID_VIEWER", None)
    result = subprocess.run(
        [sys.executable, "rapid2py.py", "-r", "-e", "demo.main"]
        + ["-i", os.path.join("examples", "irb120", "demo.mod")]
        + ["-d", os.fspath(tmp_path), "-f", "demo.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    # log: "<time> s  <instruction> <zone>  axes [...]"
    moves = [line.split() for line in result.stdout.splitlines() if " axes [" in line]
    assert [m[2] for m in moves].count("MoveL") == 14
    assert [m[2] for m in moves].count("MoveC") == 2
    # the corners z20 of the small square are passed without stopping
    assert [m[3] for m in moves].count("z20") == 3
    assert "tilted pen at [75,75,50]" in result.stdout
