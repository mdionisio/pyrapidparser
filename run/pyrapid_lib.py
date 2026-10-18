"""Functions of the standard library written in Python: mathematics, vectors, poses, bits
and strings. default/standard.sys declares the RAPID routines and calls these functions
with the data of the arguments; the angles are in degrees and the lengths in mm, as in
RAPID. The orientations are quaternions [q1, q2, q3, q4] = [w, x, y, z]."""

import datetime
import math
import random
from typing import Any, Callable, Sequence

Vector = list[float]
Quaternion = list[float]


def plain(data: Any) -> Any:
    """the value of RAPID data: numbers, strings, bools, and lists for the records"""
    value = data.Get() if hasattr(data, "Get") else data
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def call(result: Any, function: Callable[..., Any], *arguments: Any) -> None:
    """result := function(arguments) with the data of the RAPID arguments; an argument
    that is None (optional and absent) is passed as it is"""
    result.Set(function(*[plain(a) if a is not None else None for a in arguments]))


# ---------------------------------------------------------------- numbers


def sin(degree: float) -> float:
    return math.sin(math.radians(degree))


def cos(degree: float) -> float:
    return math.cos(math.radians(degree))


def tan(degree: float) -> float:
    return math.tan(math.radians(degree))


def asin(value: float) -> float:
    return math.degrees(math.asin(value))


def acos(value: float) -> float:
    return math.degrees(math.acos(value))


def atan(value: float) -> float:
    return math.degrees(math.atan(value))


def atan2(y: float, x: float) -> float:
    return math.degrees(math.atan2(y, x))


def maximum(a: float, b: float) -> float:
    return max(a, b)


def minimum(a: float, b: float) -> float:
    return min(a, b)


RAND_MAX = 32767
_generator = random.Random(1)


def rand(seed: bool, each: Any) -> int:
    """a random integer between 0 and RAND_MAX; the sequence is always the same unless
    the seed is the current time (switch \\Seed, or every \\SeedEachNTime calls)"""
    global _generator, _countdown
    if seed:
        _generator = random.Random()
    elif each is not None:
        if _countdown <= 0:
            _generator = random.Random()
            _countdown = int(each)
        _countdown -= 1
    return _generator.randint(0, RAND_MAX)


_countdown = 0


# ---------------------------------------------------------------- vectors and poses


def distance(a: Sequence[float], b: Sequence[float]) -> float:
    return math.dist(a, b)


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def cross(a: Sequence[float], b: Sequence[float]) -> Vector:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def magnitude(v: Sequence[float]) -> float:
    return math.sqrt(dot(v, v))


def normalize(q: Sequence[float]) -> Quaternion:
    """NOrient: the quaternion with norm 1"""
    norm = math.sqrt(sum(c * c for c in q))
    if norm == 0:
        raise ValueError("NOrient: the orientation is [0, 0, 0, 0]")
    return [c / norm for c in q]


def quaternion_product(a: Sequence[float], b: Sequence[float]) -> Quaternion:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return [
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ]


def rotate(q: Sequence[float], v: Sequence[float]) -> Vector:
    """the vector v rotated by the quaternion q"""
    w, x, y, z = normalize(q)
    t = [2 * c for c in cross([x, y, z], v)]
    u = cross([x, y, z], t)
    return [v[i] + w * t[i] + u[i] for i in range(3)]


def pose_vect(pose: Sequence[Any], vector: Sequence[float]) -> Vector:
    """PoseVect: the vector rotated and moved by the pose"""
    trans, rot = pose
    return [r + t for r, t in zip(rotate(rot, vector), trans)]


def pose_mult(first: Sequence[Any], second: Sequence[Any]) -> list[Any]:
    """PoseMult: the pose of the second one in the frame of the first one"""
    return [pose_vect(first, second[0]), normalize(quaternion_product(first[1], second[1]))]


def pose_inv(pose: Sequence[Any]) -> list[Any]:
    trans, rot = pose
    w, x, y, z = normalize(rot)
    inverse = [w, -x, -y, -z]
    return [[-c for c in rotate(inverse, trans)], inverse]


def euler_zyx(axis: str, rotation: Sequence[float]) -> float:
    """the Euler angle (degrees) of the rotation z, then the new y, then the new x"""
    w, x, y, z = normalize(rotation)
    if axis == "x":
        return math.degrees(math.atan2(2 * (y * z + w * x), 1 - 2 * (x * x + y * y)))
    if axis == "y":
        return math.degrees(math.asin(max(-1.0, min(1.0, -2 * (x * z - w * y)))))
    return math.degrees(math.atan2(2 * (x * y + w * z), 1 - 2 * (y * y + z * z)))


# ---------------------------------------------------------------- bits (byte: 0 to 255)


def bit_and(a: float, b: float) -> int:
    return int(a) & int(b)


def bit_or(a: float, b: float) -> int:
    return int(a) | int(b)


def bit_xor(a: float, b: float) -> int:
    return int(a) ^ int(b)


def bit_neg(a: float) -> int:
    return ~int(a) & 0xFF


def bit_left(a: float, steps: float) -> int:
    return (int(a) << int(steps)) & 0xFF


def bit_right(a: float, steps: float) -> int:
    return int(a) >> int(steps)


def bit_check(a: float, position: float) -> bool:
    """bit 1 is the least significant"""
    if not 1 <= position <= 8:
        raise ValueError("BitCheck: the bit position is 1 to 8")
    return bool(int(a) >> (int(position) - 1) & 1)


def bit_set(a: float, position: float) -> int:
    if not 1 <= position <= 8:
        raise ValueError("BitSet: the bit position is 1 to 8")
    return int(a) | 1 << (int(position) - 1)


def bit_clear(a: float, position: float) -> int:
    if not 1 <= position <= 8:
        raise ValueError("BitClear: the bit position is 1 to 8")
    return int(a) & ~(1 << (int(position) - 1))


# ---------------------------------------------------------------- strings


def dec_to_hex(text: str) -> str:
    return "%X" % int(text)


def hex_to_dec(text: str) -> int:
    return int(text, 16)


def byte_to_str(value: float, base: str) -> str:
    """base: "" decimal, "hex", "okt", "bin" or "char" (one character)"""
    number = int(value)
    if base == "hex":
        return "%X" % number
    if base == "okt":
        return "%o" % number
    if base == "bin":
        return format(number, "b")
    if base == "char":
        return chr(number)
    return str(number)


def str_to_byte(text: str, base: str) -> int:
    if base == "char":
        return ord(text[0])
    return int(text, {"hex": 16, "okt": 8, "bin": 2}.get(base, 10))


def str_memb(text: str, position: float, characters: str) -> bool:
    """is the character at the position (from 1) one of characters"""
    return 1 <= position <= len(text) and text[int(position) - 1] in characters


def str_order(first: str, second: str, order: str) -> bool:
    """first <= second when the characters are ordered as in order; the characters that
    are not in order follow the others"""

    def key(text: str) -> list[int]:
        return [order.find(c) if c in order else len(order) + ord(c) for c in text]

    return key(first) <= key(second)


def str_map(text: str, source: str, target: str) -> str:
    return text.translate({ord(f): t for f, t in zip(source, target)})


# ---------------------------------------------------------------- date and time


def get_time(field: str) -> int:
    now = datetime.datetime.now()
    return {
        "wday": now.isoweekday(),
        "hour": now.hour,
        "min": now.minute,
        "sec": now.second,
        "msec": now.microsecond // 1000,
    }[field]


def c_time() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def c_date() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")
