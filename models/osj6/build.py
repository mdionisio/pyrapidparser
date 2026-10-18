"""Build the 6 axis oblique swivel joint robot osj6: the printable parts (STL) and the
model (osj6.urdf).

The robot is a tube of diameter D. Axis 1 turns the arm around the vertical axis of
the base, the axes 2 to 5 are oblique swivel joints: the tube is cut at 45 degrees and
each piece turns on the cut plane of the previous one (joint axis at 45 degrees from
the tube). Axis 6 turns the tool flange around the tube. The pieces from the base:

    base       flat top, motor of axis 1
    shoulder   flat bottom (axis 1), 45 degree top (motor of axis 2)
    module x3  45 degree cuts at both ends, mirrored (axes 3, 4, 5): all equal
    wrist      45 degree bottom (axis 5), flat top (motor of axis 6)
    flange     the tool flange (ISO 9409-1-31.5-4-M3)

Every joint is the same: the upper piece has a hollow spigot that turns in a thin
section bearing 61808 (40 x 52 x 7 mm) of the lower piece; a printed gear (48 teeth,
module 1) on the spigot is driven by a pinion (10 teeth) of an N20 gear motor in the
lower piece. The cables pass through the spigots (bore 34 mm). A hatch on the side of
each piece gives access to the gear, the motor and the cables.

The geometry is parametric (see the constants below). Needs manifold3d and numpy (not
dependencies of the project):

    pip install manifold3d numpy
    python models/osj6/build.py

writes the STL files (mm) in models/osj6/parts/ and the model in models/osj6.urdf.
The pieces are written in the orientation of printing: the face of the bearing housing
on the bed. The masses come from the volumes of the parts (PLA) plus motors and
bearings.
"""

import math
import os
import sys

import numpy as np

try:
    from manifold3d import CrossSection, Manifold
except ImportError:  # pragma: no cover
    print("the parts need manifold3d: pip install manifold3d", file=sys.stderr)
    sys.exit(1)

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "parts")
URDF = os.path.join(os.path.dirname(HERE), "osj6.urdf")

# geometry (mm)
D = 80.0  # outer diameter of the tube
WALL = 2.5  # wall of the tube
ANGLE = math.radians(45)  # joint axis from the tube axis
MODULE = 120.0  # module: distance of the joint centers along the tube
SHOULDER = 80.0  # shoulder and wrist: flat end to the center of the 45 degree joint
BASE = 70.0  # height of the axis 1 above the floor
TOOL = 10.0  # tool flange (tool0) above the axis 6 joint plane
SEGMENTS = 96

# joint (in the joint frame: z along the axis, 0 in the middle of the gap between the
# pieces; the lower piece, with the motor, is at z < 0)
GAP = 0.5  # half gap
PLATE = 4.0  # end plates
BORE = 17.0  # radius of the cable bore
SPIGOT = 20.0  # spigot: bearing seat (61808: 40 x 52 x 7)
COLLAR = 22.5  # collar of the spigot on the inner ring of the bearing
BEARING_OUT = 26.0
BEARING_IN_Z = (-9.5, -2.5)
HOUSING = 33.0  # outer radius of the bearing housing
CAP = 33.5  # bearing cap, in a counterbore of the plate
CAP_IN = 23.0
SCREW_RADIUS = 29.75  # 4 screws M2.5 of the cap
GEAR_TEETH, PINION_TEETH, GEAR_MODULE = 48, 10, 1.0
GEAR_SHIFT = 0.4  # profile shift: + on the pinion, - on the gear (no undercut)
GEAR_Z = (-17.5, -11.5)  # face of the gear and the pinion
CENTER = GEAR_MODULE * (GEAR_TEETH + PINION_TEETH) / 2  # motor axis from the joint axis

# N20 gear motor with encoder (12 x 10 mm, shaft 3 mm with a flat)
N20_W, N20_H = 12.0, 10.0
N20_Z = (-50.5, -18.5)  # encoder bottom, gearbox top
N20_GEARBOX = 9.0

# masses
PLA = 1.24e-3  # g/mm^3, solid
BEARING_MASS = 23.0  # g, 61808
MOTOR_MASS = 15.0  # g, N20 with encoder and wires

R = D / 2


# transforms (4x4, mm)


def rot_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    t = np.eye(4)
    t[1:3, 1:3] = [[c, -s], [s, c]]
    return t


def rot_z(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    t = np.eye(4)
    t[0:2, 0:2] = [[c, -s], [s, c]]
    return t


def move(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> np.ndarray:
    t = np.eye(4)
    t[:3, 3] = (x, y, z)
    return t


def place(solid: Manifold, t: np.ndarray) -> Manifold:
    return solid.transform(t[:3, :])


def rpy(t: np.ndarray) -> tuple[float, float, float]:
    """URDF roll, pitch, yaw of a rotation (R = Rz(yaw) Ry(pitch) Rx(roll))"""
    r = t[:3, :3]
    pitch = math.asin(max(-1.0, min(1.0, -r[2, 0])))
    if abs(r[2, 0]) < 1 - 1e-9:
        return math.atan2(r[2, 1], r[2, 2]), pitch, math.atan2(r[1, 0], r[0, 0])
    return math.atan2(-r[1, 2], r[1, 1]), pitch, 0.0


# solids


def cylinder(radius: float, z0: float, z1: float, inner: float = 0.0) -> Manifold:
    solid = Manifold.cylinder(z1 - z0, radius, radius, SEGMENTS).translate((0, 0, z0))
    if inner > 0:
        solid = solid - Manifold.cylinder(z1 - z0 + 2, inner, inner, SEGMENTS).translate(
            (0, 0, z0 - 1)
        )
    return solid


def box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Manifold:
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def half_space(t: np.ndarray, above: bool) -> Manifold:
    """the side z > 0 (above) or z < 0 of the frame t, as a large box"""
    size = 1000.0
    solid = (
        box(-size, size, -size, size, 0, size) if above else box(-size, size, -size, size, -size, 0)
    )
    return place(solid, t)


def involute_gear(teeth: int, shift: float, bore: float) -> CrossSection:
    """involute spur gear (pressure angle 20 degrees, module GEAR_MODULE) with a bore"""
    m, alpha = GEAR_MODULE, math.radians(20)
    rp = m * teeth / 2
    rb = rp * math.cos(alpha)
    ra = rp + m * (1 + shift)
    rf = rp - m * (1.25 - shift)

    def inv(a: float) -> float:
        return math.tan(a) - a

    half = (math.pi / 2 + 2 * shift * math.tan(alpha)) / teeth  # half tooth at the pitch

    def half_angle(r: float) -> float:
        r = max(r, rb)
        return half + inv(alpha) - inv(math.acos(rb / r))

    radii = [rf + (ra - rf) * i / 12 for i in range(13)]
    points = []
    for i in range(teeth):
        center = 2 * math.pi * i / teeth
        flank = [(r, center - half_angle(r)) for r in radii]
        flank += [(r, center + half_angle(r)) for r in reversed(radii)]
        # root arc to the next tooth
        start = center + half_angle(rf)
        end = 2 * math.pi * (i + 1) / teeth - half_angle(rf)
        flank += [(rf, start + (end - start) * k / 4) for k in range(1, 4)]
        points += [(r * math.cos(a), r * math.sin(a)) for r, a in flank]
    gear = CrossSection([points])
    if bore > 0:
        gear = gear - CrossSection.circle(bore, SEGMENTS)
    return gear


# the two sides of a joint, in the joint frame


def tube_down(t_joint: np.ndarray, t_tube: np.ndarray) -> np.ndarray:
    """direction of the lower tube (from the joint into the piece) in the joint plane"""
    axis = np.linalg.inv(t_joint)[:3, :3] @ t_tube[:3, 2]
    d = -axis[:2]
    if np.linalg.norm(d) < 1e-9:
        return np.array([0.0, -1.0])
    return d / np.linalg.norm(d)


def motor_frame(direction: np.ndarray) -> np.ndarray:
    """the motor axis in the joint frame: parallel to the joint axis, at CENTER"""
    angle = math.atan2(direction[1], direction[0])
    return rot_z(angle) @ move(CENTER)


def pinion_phase(direction: np.ndarray) -> np.ndarray:
    """the pinion turned to mesh with the gear at the zero position of the joint"""
    pitch = 2 * math.pi / GEAR_TEETH
    offset = math.atan2(direction[1], direction[0]) % pitch
    return rot_z(math.pi / PINION_TEETH - offset * GEAR_TEETH / PINION_TEETH)


def lower_side(direction: np.ndarray) -> Manifold:
    """lower piece (z < 0): end plate, bearing housing and cap seat, motor bracket"""
    plate = cylinder(D, -GAP - PLATE, -GAP, CAP_IN + 3)
    housing = cylinder(HOUSING, BEARING_IN_Z[0] - 1.5, -GAP - PLATE, CAP_IN)
    seat = cylinder(BEARING_OUT, BEARING_IN_Z[0], 0)
    counterbore = cylinder(CAP + 0.4, -GAP - 2.0, 0)
    side = (plate + housing) - seat - counterbore
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        hole = cylinder(1.05, BEARING_IN_Z[0] - 1.5 - 1, 0).translate(
            (SCREW_RADIUS * math.cos(a), SCREW_RADIUS * math.sin(a), 0)
        )
        side = side - hole
    # bracket: a sleeve around the gearbox, joined to the wall by a web
    t = motor_frame(direction)
    z0, z1 = N20_Z[1] - 12.0, N20_Z[1]
    sleeve = box(-N20_W / 2 - 2, N20_W / 2 + 2, -N20_H / 2 - 2, N20_H / 2 + 2, z0, z1)
    pocket = box(
        -N20_W / 2 - 0.15, N20_W / 2 + 0.15, -N20_H / 2 - 0.15, N20_H / 2 + 0.15, z0 - 1, z1 + 1
    )
    # the web on one side only: the cables pass on the other
    web = box(-3, 3, 0, 80, z0, z1 - 4)
    return side + place(sleeve + web - pocket, t)


def upper_side() -> Manifold:
    """upper piece (z > 0): end plate, collar and spigot with a key for the gear"""
    plate = cylinder(D, GAP, GAP + PLATE)
    collar = cylinder(COLLAR, BEARING_IN_Z[1], GAP + PLATE)
    spigot = cylinder(SPIGOT, GEAR_Z[0], BEARING_IN_Z[1])
    key = box(SPIGOT - 0.5, SPIGOT + 1.0, -1.5, 1.5, GEAR_Z[0], BEARING_IN_Z[0])
    return (plate + collar + spigot + key) - cylinder(BORE, GEAR_Z[0] - 1, GAP + PLATE + 1)


def gear() -> Manifold:
    """gear on the spigot: a hub on the inner ring of the bearing and the teeth"""
    teeth = Manifold.extrude(involute_gear(GEAR_TEETH, -GEAR_SHIFT, 0), GEAR_Z[1] - GEAR_Z[0])
    teeth = teeth.translate((0, 0, GEAR_Z[0]))
    hub = cylinder(COLLAR - 0.5, GEAR_Z[1], BEARING_IN_Z[0])
    slot = box(SPIGOT - 1.0, SPIGOT + 1.3, -1.7, 1.7, GEAR_Z[0] - 1, BEARING_IN_Z[0] + 1)
    return (teeth + hub) - cylinder(SPIGOT + 0.1, GEAR_Z[0] - 1, BEARING_IN_Z[0] + 1) - slot


def pinion() -> Manifold:
    """pinion on the D shaft of the N20, in the motor frame"""
    teeth = Manifold.extrude(involute_gear(PINION_TEETH, GEAR_SHIFT, 0), GEAR_Z[1] - GEAR_Z[0])
    shaft = cylinder(1.55, GEAR_Z[0] - 1, GEAR_Z[1] + 1) - box(
        1.0, 3, -3, 3, GEAR_Z[0] - 2, GEAR_Z[1] + 2
    )
    return teeth.translate((0, 0, GEAR_Z[0])) - shaft


def cap() -> Manifold:
    """bearing cap, screwed on the lower piece"""
    ring = cylinder(CAP, -GAP - 2.0, -GAP, CAP_IN)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        ring = ring - cylinder(1.4, -GAP - 3, 0).translate(
            (SCREW_RADIUS * math.cos(a), SCREW_RADIUS * math.sin(a), 0)
        )
    return ring


def bearing() -> Manifold:
    """61808 (not printed)"""
    return cylinder(BEARING_OUT, BEARING_IN_Z[0], BEARING_IN_Z[1], SPIGOT)


def motor() -> Manifold:
    """N20 gear motor with encoder (not printed), in the motor frame"""
    z0, z1 = N20_Z
    w, h = N20_W / 2, N20_H / 2
    gearbox = box(-w, w, -h, h, z1 - N20_GEARBOX, z1)
    can = cylinder(w, z0 + 8, z1 - N20_GEARBOX) ^ box(-w, w, -h, h, z0, z1)
    encoder = cylinder(w - 1, z0, z0 + 8)
    shaft = cylinder(1.5, z1, GEAR_Z[1] + 0.5)
    return gearbox + can + encoder + shaft


# the pieces: a tube between two joints (frames in the tube frame, z along the tube)


class Piece:
    def __init__(self, name: str, lower: np.ndarray, upper: np.ndarray, length: float):
        self.name = name
        self.lower = lower  # lower joint frame in the tube frame
        self.upper = upper  # upper joint frame (the motor of the next axis)
        self.length = length

    def tube_region(self, radius: float) -> Manifold:
        tube = cylinder(radius, -200, self.length + 200)
        tube = tube ^ half_space(self.lower @ move(z=GAP), True)
        return tube ^ half_space(self.upper @ move(z=-GAP), False)

    def hatch_window(self, radius: float, margin: float) -> Manifold:
        """the window on the long side of the tube, in front of the motor"""
        frame = self.upper @ motor_frame(tube_down(self.upper, np.eye(4)))
        motor = (frame @ move(z=N20_Z[0]))[:3, 3]
        angle = math.atan2(motor[1], motor[0])
        ends = []
        for frame, sign in ((self.lower, 1), (self.upper, -1)):
            # the cut plane on the side of the window
            n = frame[:3, 2]
            p = frame[:3, 3]
            side = np.array([math.cos(angle), math.sin(angle), 0]) * R
            ends.append(p[2] - (n[:2] @ (side[:2] - p[:2])) / n[2])
        z0, z1 = ends[0] + 22 - margin, ends[1] - 24 + margin
        z0, z1 = max(z0, (z0 + z1) / 2 - 45 - margin), min(z1, (z0 + z1) / 2 + 45 + margin)
        half_width = 24 + margin
        window = box(0, radius + 5, -half_width, half_width, z0, z1)
        return place(window, rot_z(angle))

    def solid(self) -> Manifold:
        shell = self.tube_region(R) - cylinder(R - WALL, -300, self.length + 300)
        lower = place(upper_side(), self.lower) ^ place(cylinder(R, -300, 300), np.eye(4))
        spigot = place(upper_side() - half_space(move(z=GAP), True), self.lower)
        upper = lower_side(tube_down(self.upper, np.eye(4)))
        upper = place(upper, self.upper) ^ self.tube_region(R)
        return (shell - self.hatch_window(R + 1, 0)) + lower + spigot + upper

    def hatch(self) -> Manifold:
        cover = cylinder(R + 2, -300, self.length + 300) - cylinder(
            R + 0.2, -300, self.length + 300
        )
        return cover ^ self.hatch_window(R + 3, 4) ^ self.tube_region(R + 3)


def shoulder() -> Piece:
    return Piece("shoulder", np.eye(4), move(z=SHOULDER) @ rot_x(ANGLE), SHOULDER)


def module() -> Piece:
    return Piece("module", rot_x(ANGLE), move(z=MODULE) @ rot_z(math.pi) @ rot_x(ANGLE), MODULE)


def wrist() -> Piece:
    return Piece("wrist", rot_x(ANGLE), move(z=SHOULDER), SHOULDER)


def base() -> Manifold:
    """base: tube from the floor to the axis 1, a foot with 4 holes, the motor of axis 1"""
    top = move(z=BASE)
    shell = cylinder(R, 0, BASE - GAP, R - WALL)
    foot = cylinder(70, 0, 6, 10)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        foot = foot - cylinder(2.75, -1, 7).translate((58 * math.cos(a), 58 * math.sin(a), 0))
    side = place(lower_side(np.array([0.0, -1.0])), top) ^ cylinder(R, 0, BASE)
    cable = place(Manifold.cylinder(30, 8, 8, SEGMENTS), rot_x(-math.pi / 2)).translate((0, 0, 20))
    return shell + foot + side - cable


def flange() -> Manifold:
    """tool flange (ISO 9409-1-31.5-4-M3): spigot, plate and the tool face at TOOL"""
    body = (upper_side() ^ cylinder(R, -100, 100)) + cylinder(25, GAP + PLATE, TOOL)
    body = body - cylinder(10, GAP, TOOL + 1)
    for k in range(4):
        a = k * math.pi / 2
        body = body - cylinder(1.6, GAP + PLATE - 1, TOOL + 1).translate(
            (15.75 * math.cos(a), 15.75 * math.sin(a), 0)
        )
    return body


# mass properties


def mesh(solid: Manifold) -> tuple[np.ndarray, np.ndarray]:
    m = solid.to_mesh()
    return np.asarray(m.vert_properties)[:, :3].astype(float), np.asarray(m.tri_verts)


def mass_properties(solid: Manifold, density: float) -> tuple[float, np.ndarray, np.ndarray]:
    """mass (g), center of mass (mm), inertia at the center of mass (g mm^2)"""
    vertices, triangles = mesh(solid)
    a, b, c = (vertices[triangles[:, i]] for i in range(3))
    volume = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6
    total = volume.sum()
    center = ((a + b + c) * volume[:, None]).sum(axis=0) / 4 / total
    # second moments of the tetrahedra (origin, a, b, c)
    second = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            s = (
                2 * (a[:, i] * a[:, j] + b[:, i] * b[:, j] + c[:, i] * c[:, j])
                + a[:, i] * b[:, j]
                + a[:, j] * b[:, i]
                + a[:, i] * c[:, j]
                + a[:, j] * c[:, i]
                + b[:, i] * c[:, j]
                + b[:, j] * c[:, i]
            )
            second[i, j] = (volume * s).sum() / 20
    second = second - total * np.outer(center, center)
    inertia = np.trace(second) * np.eye(3) - second
    return total * density, center, inertia * density


class Body:
    """mass properties in a link frame (g, mm)"""

    def __init__(self) -> None:
        self.parts: list[tuple[float, np.ndarray, np.ndarray]] = []

    def add(self, solid: Manifold, t: np.ndarray, density: float = PLA) -> None:
        self.parts.append(mass_properties(place(solid, t), density))

    def add_point(self, mass: float, t: np.ndarray, solid: Manifold) -> None:
        """a part of known mass, its inertia from its shape"""
        m, c, i = mass_properties(place(solid, t), 1.0)
        self.parts.append((mass, c, i * mass / m))

    def total(self) -> tuple[float, np.ndarray, np.ndarray]:
        mass = sum(p[0] for p in self.parts)
        center = sum(p[0] * p[1] for p in self.parts) / mass
        inertia = np.zeros((3, 3))
        for m, c, i in self.parts:
            d = c - center
            inertia += i + m * (d @ d * np.eye(3) - np.outer(d, d))
        return mass, center, inertia


# output


def write_stl(solid: Manifold, path: str) -> None:
    vertices, triangles = mesh(solid)
    with open(path, "wb") as f:
        f.write(b"osj6".ljust(80, b" "))
        f.write(np.uint32(len(triangles)).tobytes())
        records = np.zeros(
            len(triangles), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]
        )
        tri = vertices[triangles]
        normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        normal /= np.maximum(np.linalg.norm(normal, axis=1), 1e-12)[:, None]
        records["n"] = normal
        records["v"] = tri
        f.write(records.tobytes())


def origin(t: np.ndarray, scale: float = 0.001) -> str:
    xyz = " ".join("%.9g" % (0.0 if abs(v) < 1e-9 else v * scale) for v in t[:3, 3])
    angles = " ".join("%.9g" % (0.0 if abs(v) < 1e-12 else v) for v in rpy(t))
    return '<origin xyz="%s" rpy="%s"/>' % (xyz, angles)


def urdf_link(name: str, visuals: list[tuple[str, np.ndarray, str]], body: Body) -> str:
    mass, center, inertia = body.total()
    lines = ['  <link name="%s">' % name]
    for part, t, material in visuals:
        lines += [
            "    <visual>",
            "      " + origin(t),
            '      <geometry><mesh filename="package://osj6/parts/%s.stl" scale="0.001 0.001 0.001"/></geometry>'
            % part,
            '      <material name="%s"/>' % material,
            "    </visual>",
        ]
    i = inertia * 1e-9  # g mm^2 -> kg m^2
    lines += [
        "    <inertial>",
        '      <origin xyz="%s" rpy="0 0 0"/>' % " ".join("%.6g" % (v * 0.001) for v in center),
        '      <mass value="%.4f"/>' % (mass * 0.001),
        '      <inertia ixx="%.4g" ixy="%.4g" ixz="%.4g" iyy="%.4g" iyz="%.4g" izz="%.4g"/>'
        % (i[0, 0], i[0, 1], i[0, 2], i[1, 1], i[1, 2], i[2, 2]),
        "    </inertial>",
        "  </link>",
    ]
    return "\n".join(lines)


def urdf_joint(name: str, parent: str, child: str, t: np.ndarray) -> str:
    return "\n".join(
        [
            '  <joint name="%s" type="revolute">' % name,
            '    <parent link="%s"/>' % parent,
            '    <child link="%s"/>' % child,
            "    " + origin(t),
            '    <axis xyz="0 0 1"/>',
            '    <limit lower="-2.9671" upper="2.9671" velocity="1.0472" effort="0"/>',
            "  </joint>",
        ]
    )


def main() -> int:
    os.makedirs(PARTS, exist_ok=True)
    pieces = [shoulder(), module(), wrist()]
    flip = rot_x(math.pi) @ move(z=GAP)  # print frame: the housing face on the bed

    printed = {
        "base": base(),
        "flange": flange(),
        "gear": gear(),
        "pinion": pinion(),
        "cap": cap(),
    }
    print_frame = {}
    for piece in pieces:
        t = piece.upper @ flip
        print_frame[piece.name] = t
        printed[piece.name] = place(piece.solid(), np.linalg.inv(t))
        printed[piece.name + "_hatch"] = place(piece.hatch(), np.linalg.inv(t))
    others = {"motor": motor(), "bearing": bearing()}
    for name, solid in list(printed.items()) + list(others.items()):
        write_stl(solid, os.path.join(PARTS, name + ".stl"))
        mass = solid.volume() * PLA
        print("%-16s %6.1f g  %s" % (name + ".stl", mass, "printed" if name in printed else ""))

    def joint_parts(body: Body, visuals: list, t_joint: np.ndarray, direction: np.ndarray) -> None:
        """the parts of the lower side of a joint: bearing, cap, motor, pinion"""
        m = t_joint @ motor_frame(direction)
        p = m @ pinion_phase(direction)
        visuals += [
            ("bearing", t_joint, "steel"),
            ("cap", t_joint, "print"),
            ("motor", m, "dark"),
            ("pinion", p, "gear"),
        ]
        body.add_point(BEARING_MASS, t_joint, bearing())
        body.add(cap(), t_joint)
        body.add_point(MOTOR_MASS, m, motor())
        body.add(pinion(), p)

    links = []
    # base
    body, visuals = Body(), [("base", np.eye(4), "print")]
    body.add(printed["base"], np.eye(4))
    joint_parts(body, visuals, move(z=BASE), np.array([0.0, -1.0]))
    links.append(("base_link", visuals, body))
    # shoulder, modules, wrist: the link frame is the lower joint
    chain = [pieces[0], pieces[1], pieces[1], pieces[1], pieces[2]]
    for n, piece in enumerate(chain, start=1):
        to_link = np.linalg.inv(piece.lower)
        t = to_link @ print_frame[piece.name]
        body = Body()
        visuals = [
            (piece.name, t, "print"),
            (piece.name + "_hatch", t, "print"),
            ("gear", np.eye(4), "gear"),
        ]
        body.add(printed[piece.name], t)
        body.add(printed[piece.name + "_hatch"], t)
        body.add(gear(), np.eye(4))
        joint_parts(body, visuals, to_link @ piece.upper, tube_down(piece.upper, np.eye(4)))
        links.append(("link_%d" % n, visuals, body))
    body = Body()
    body.add(flange(), np.eye(4))
    body.add(gear(), np.eye(4))
    links.append(("link_6", [("flange", np.eye(4), "print"), ("gear", np.eye(4), "gear")], body))

    joints = [move(z=BASE)] + [np.linalg.inv(p.lower) @ p.upper for p in chain]
    # tool0 parallel to the base at the zero position (the modules turn by 180 degrees)
    zero = np.eye(4)
    for t in joints:
        zero = zero @ t
    tool = move(z=TOOL) @ np.linalg.inv(np.r_[np.c_[zero[:3, :3], np.zeros(3)], [[0, 0, 0, 1]]])
    text = [
        '<?xml version="1.0"?>',
        "<!--",
        "  osj6: 6 axis oblique swivel joint robot (tube %g mm, joints at 45 degrees)," % D,
        "  generated by models/osj6/build.py: do not edit, change the script and run it.",
        "  Masses from the volumes of the printed parts (PLA) plus motors and bearings.",
        "-->",
        '<robot name="osj6">',
        '  <material name="print"><color rgba="0.95 0.55 0.1 1"/></material>',
        '  <material name="gear"><color rgba="0.2 0.45 0.85 1"/></material>',
        '  <material name="steel"><color rgba="0.7 0.7 0.72 1"/></material>',
        '  <material name="dark"><color rgba="0.2 0.2 0.2 1"/></material>',
        '  <link name="base"/>',
        '  <joint name="base_link-base" type="fixed">',
        '    <parent link="base_link"/>',
        '    <child link="base"/>',
        '    <origin xyz="0 0 0" rpy="0 0 0"/>',
        "  </joint>",
    ]
    for i, (name, visuals, body) in enumerate(links):
        text.append(urdf_link(name, visuals, body))
        if i < 6:
            text.append(urdf_joint("joint_%d" % (i + 1), name, "link_%d" % (i + 1), joints[i]))
    text += [
        '  <link name="tool0"/>',
        '  <joint name="joint_6-tool0" type="fixed">',
        '    <parent link="link_6"/>',
        '    <child link="tool0"/>',
        "    " + origin(tool),
        "  </joint>",
        "</robot>",
        "",
    ]
    with open(URDF, "w") as f:
        f.write("\n".join(text))
    total = sum(body.total()[0] for _, _, body in links)
    print("%s: %.0f g" % (os.path.relpath(URDF, os.getcwd()), total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
