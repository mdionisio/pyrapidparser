"""rapid2py test: .mod -> rapid2py -> .py, the generated module must be valid Python.

Each conversion runs rapid2py.py in its own process, as from the command line
(standard symbols of default/*.sys included), because the symbol table of
run.pyrapid is a process-wide singleton.
"""

import glob
import os
import pathlib
import subprocess
import sys
from typing import Any

import pytest

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(PROJECT_DIR, "test")
# *.ast.mod / *.source.mod / rapid_program.mod are outputs of other tests
MOD_FILES = sorted(
    f
    for f in glob.glob(os.path.join(TEST_DIR, "*.mod"))
    if not f.endswith((".ast.mod", ".source.mod", "rapid_program.mod"))
)

# known limitations of rapid2py: the conversion itself fails
KNOWN_FAILURES = {
    "rapid1.mod": "'list' object has no attribute 'GetElem'",
    "test1.mod": "unknown data type (GetSymbol returns None)",
    "test6.mod": "symbol pippo already defined",
    "test7.mod": "symbol pippo already defined",
    "test8.mod": "Symbol p1 has to be a constant variable",
    "test10.mod": "rapid_struct.Set with a list of wrong size",
    "test20.mod": "symbol TPWrite already defined (clash with default/standard.sys)",
}


def mod_param(path: str) -> Any:
    name = os.path.basename(path)
    marks = []
    if name in KNOWN_FAILURES:
        marks.append(pytest.mark.xfail(reason=KNOWN_FAILURES[name], strict=True))
    return pytest.param(path, id=name, marks=marks)


@pytest.mark.parametrize("path", [mod_param(f) for f in MOD_FILES])
def test_rapid2py_generates_valid_python(path: str, tmp_path: pathlib.Path) -> None:
    outdir = os.fspath(tmp_path)
    result = subprocess.run(
        [sys.executable, "rapid2py.py", "-i", path, "-d", outdir, "-f", "rapid_program.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    # stdout is the (long) AST dump made on error, stderr ends with the traceback
    assert result.returncode == 0, result.stderr[-2000:]

    pyfile = os.path.join(outdir, "rapid_program.py")
    with open(pyfile, "r") as f:
        source = f.read()
    compile(source, pyfile, "exec")
