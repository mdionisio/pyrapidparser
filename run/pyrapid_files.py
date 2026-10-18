"""Files and directories of the RAPID instructions (Open, Write, ReadStr, MakeDir, ...).

The iodev data holds the name of the handle of the open file ("iodev1"); the files are
in the registry of this module. The paths of the controller "HOME:/dir/file" are
relative to the folder of the environment variable PYRAPID_HOME (default: the current
folder), "TEMP:" to the temporary folder. The serial channels ("com1:") are not
supported. The text is read and written as latin-1: a character is a byte."""

import os
import shutil
import tempfile
from typing import Any, Optional

from run.pyrapid_lib import LibraryError

EOF_NUM = 9.998e36
EOF_BIN = -1

_files: dict[str, Any] = {}
_directories: dict[str, list[str]] = {}
_counter = 0


def path_of(path: str) -> str:
    """the file of a path of the controller"""
    prefix, colon, rest = path.partition(":")
    if colon and len(prefix) > 1 and prefix.isalnum():
        root = {
            "HOME": os.environ.get("PYRAPID_HOME", os.getcwd()),
            "TEMP": tempfile.gettempdir(),
        }.get(prefix.upper())
        if root is None:
            raise LibraryError("ERR_FILEOPEN", "%s: unknown device %s:" % (path, prefix))
        return os.path.join(root, rest.lstrip("/\\"))
    return path


def handle(device: str) -> Any:
    if device not in _files:
        raise LibraryError("ERR_FILEACC", "the file %s is not open" % (device or "?",))
    return _files[device]


def open_file(path: str, mode: str, binary: bool) -> str:
    """mode: "read", "write" (default) or "append"; the binary files are read and written"""
    global _counter
    real = path_of(path)
    python_mode = {"read": "r", "write": "w", "append": "a"}[mode]
    if binary:
        python_mode = "r+b" if os.path.exists(real) and mode != "write" else "w+b"
        if mode == "append":
            python_mode = "a+b"
    try:
        stream = (
            open(real, python_mode)
            if binary
            else open(real, python_mode, encoding="latin-1", newline="")
        )
    except OSError as error:
        raise LibraryError("ERR_FILEOPEN", "cannot open %s: %s" % (path, error.strerror)) from None
    _counter += 1
    name = "iodev%d" % (_counter,)
    _files[name] = stream
    return name


def close(device: str) -> None:
    handle(device).close()
    del _files[device]


def rewind(device: str) -> None:
    handle(device).seek(0)


def clear_buffer(device: str) -> None:
    handle(device)


def write(device: str, text: str, newline: bool) -> None:
    stream = handle(device)
    try:
        stream.write(text + ("\n" if newline else ""))
        stream.flush()
    except (OSError, ValueError) as error:
        raise LibraryError("ERR_FILEACC", "cannot write: %s" % (error,)) from None


def write_bin(device: str, data: list[Any], count: int) -> None:
    stream = handle(device)
    stream.write(bytes(int(b) & 0xFF for b in data[: int(count)]))
    stream.flush()


def write_str_bin(device: str, text: str) -> None:
    stream = handle(device)
    stream.write(text.encode("latin-1"))
    stream.flush()


def read_str(device: str, remove_cr: bool, discard_headers: bool) -> str:
    """the next line, "EOF" at the end of the file"""
    stream = handle(device)
    line: str = stream.readline()
    while discard_headers and line.startswith("#"):
        line = stream.readline()
    if line == "":
        return "EOF"
    line = line.rstrip("\n")
    return line.rstrip("\r") if remove_cr else line


def read_num(device: str, delimiter: Optional[str]) -> float:
    """the next number: the numbers are separated by white space and by the delimiter
    (a character); EOF_NUM at the end of the file"""
    stream = handle(device)
    separators = " \t\r\n" + (delimiter or "")
    token = ""
    while True:
        char = stream.read(1)
        if char == "":
            break
        if char in separators:
            if token:
                break
            continue
        token += char
    if token == "":
        return EOF_NUM
    try:
        return float(token)
    except ValueError:
        raise LibraryError("ERR_RCVDATA", "ReadNum: %r is not a number" % (token,)) from None


def read_bin(device: str) -> int:
    byte = handle(device).read(1)
    return byte[0] if byte else EOF_BIN


def read_str_bin(device: str, count: float) -> str:
    data: bytes = handle(device).read(int(count))
    return data.decode("latin-1") if data else "EOF"


# ---------------------------------------------------------------- file system


def remove_file(path: str) -> None:
    try:
        os.remove(path_of(path))
    except OSError as error:
        raise LibraryError("ERR_FILEACC", "cannot remove %s: %s" % (path, error.strerror)) from None


def rename_file(old: str, new: str) -> None:
    _move(old, new, os.rename, "rename")


def copy_file(old: str, new: str) -> None:
    _move(old, new, shutil.copyfile, "copy")


def _move(old: str, new: str, action: Any, verb: str) -> None:
    source, target = path_of(old), path_of(new)
    if not os.path.exists(source):
        raise LibraryError("ERR_FILEACC", "cannot %s %s: it does not exist" % (verb, old))
    if os.path.exists(target):
        raise LibraryError("ERR_FILEEXIST", "cannot %s to %s: it exists" % (verb, new))
    try:
        action(source, target)
    except OSError as error:
        raise LibraryError(
            "ERR_FILEACC", "cannot %s %s: %s" % (verb, old, error.strerror)
        ) from None


def make_dir(path: str) -> None:
    try:
        os.mkdir(path_of(path))
    except OSError as error:
        raise LibraryError("ERR_FILEACC", "cannot create %s: %s" % (path, error.strerror)) from None


def remove_dir(path: str) -> None:
    try:
        os.rmdir(path_of(path))
    except OSError as error:
        raise LibraryError("ERR_FILEACC", "cannot remove %s: %s" % (path, error.strerror)) from None


def is_file(path: str, kind: str) -> bool:
    """kind: "" (any), "directory", "regfile", "symlink", "fifo", "socket"..."""
    import stat

    try:
        mode = os.lstat(path_of(path)).st_mode
    except OSError:
        return False
    tests = {
        "": lambda m: True,
        "directory": stat.S_ISDIR,
        "regfile": stat.S_ISREG,
        "symlink": stat.S_ISLNK,
        "fifo": stat.S_ISFIFO,
        "socket": stat.S_ISSOCK,
        "blockspecfile": stat.S_ISBLK,
        "charspecfile": stat.S_ISCHR,
    }
    return bool(tests[kind](mode))


def file_size(path: str) -> int:
    try:
        return os.path.getsize(path_of(path))
    except OSError as error:
        raise LibraryError("ERR_FILEACC", "cannot read %s: %s" % (path, error.strerror)) from None


def open_dir(path: str) -> str:
    global _counter
    try:
        entries = sorted(os.listdir(path_of(path)))
    except OSError as error:
        raise LibraryError("ERR_FILEOPEN", "cannot open %s: %s" % (path, error.strerror)) from None
    _counter += 1
    name = "dir%d" % (_counter,)
    _directories[name] = entries
    return name


def read_dir(device: str) -> Optional[str]:
    """the next entry of the directory, None at the end"""
    if device not in _directories:
        raise LibraryError("ERR_FILEACC", "the directory %s is not open" % (device,))
    entries = _directories[device]
    return entries.pop(0) if entries else None


def close_dir(device: str) -> None:
    if _directories.pop(device, None) is None:
        raise LibraryError("ERR_FILEACC", "the directory %s is not open" % (device,))
