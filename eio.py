"""I/O signals of the controller configuration (EIO.cfg).

On the robot the signals are defined in the I/O configuration, not in the RAPID
program: the program uses them by name as installed data objects of type signaldi,
signaldo, signalgi, signalgo, signalai or signalao. This module reads the signals
(name and type) from the section EIO_SIGNAL of an ABB configuration file:

    EIO:CFG_1.0:6:1::
    #
    EIO_SIGNAL:

          -Name "doGripper" -SignalType "DO" -Device "d652" -DeviceMap "0"

          -Name "giCount" -SignalType "GI" -Device "d652" -DeviceMap "8-15"

rapidvalidate and rapid2py take the file with the option --eio.
"""

import re

SIGNAL_TYPES = {
    "DI": "signaldi",
    "DO": "signaldo",
    "GI": "signalgi",
    "GO": "signalgo",
    "AI": "signalai",
    "AO": "signalao",
}


class EioError(Exception):
    pass


def parse(text: str, filename: str = "EIO.cfg") -> dict[str, str]:
    """signal name -> RAPID type (signaldi, ...) of the section EIO_SIGNAL"""
    signals: dict[str, str] = {}
    section = None
    entries: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        header = re.match(r"^([A-Z][A-Z0-9_]*):\s*$", stripped)
        if header and not line[:1].isspace():
            section = header.group(1)
            continue
        if section not in ("EIO_SIGNAL", "EIO_USER_SIGNAL"):
            continue
        if stripped.startswith("-Name") or not entries:
            entries.append(stripped)
        else:
            entries[-1] += " " + stripped
    for entry in entries:
        attributes = {
            key.lower(): quoted or plain
            for key, quoted, plain in re.findall(r'-(\w+)\s+(?:"([^"]*)"|(\S+))', entry)
        }
        name = attributes.get("name")
        kind = attributes.get("signaltype", "").upper()
        if not name:
            raise EioError("%s: signal without -Name: %s" % (filename, entry))
        if kind not in SIGNAL_TYPES:
            raise EioError("%s: signal %s: unknown -SignalType %s" % (filename, name, kind))
        if name.lower() in (n.lower() for n in signals):
            raise EioError("%s: signal %s defined twice" % (filename, name))
        signals[name] = SIGNAL_TYPES[kind]
    return signals


def load(paths: list[str]) -> dict[str, str]:
    signals: dict[str, str] = {}
    for path in paths:
        with open(path, "r") as f:
            for name, kind in parse(f.read(), path).items():
                if name.lower() in (n.lower() for n in signals):
                    raise EioError("%s: signal %s defined twice" % (path, name))
                signals[name] = kind
    return signals
